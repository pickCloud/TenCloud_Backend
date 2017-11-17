from collections import defaultdict

from service.base import BaseService
from tornado.gen import coroutine


class PermissionTemplateService(BaseService):
    table = 'permission_template'
    fields = """
            id, name, cid, permissions, access_servers, access_projects,
            access_projects, access_filehub
            """

    @coroutine
    def get_permission_detail(self, id):
        source_id_sql = """
                        SELECT permissions, access_servers, access_projects, access_filehub
                        FROM permission_template WHERE id=%s LIMIT 1
                        """
        cur = yield self.db.execute(source_id_sql, [id])
        id_data = cur.fetchone()

        self.log.info(id_data)

        permission_ids = '({ids})'.format(ids=id_data['permissions'])
        project_ids = '({ids})'.format(ids=id_data['access_projects'])
        server_ids = '({ids})'.format(ids=id_data['access_servers'])
        filehub_ids = '({ids})'.format(ids=id_data['access_filehub'])

        permission_data = yield self._get_permission_detail(fields='id, name, `group`', table='permission', params=permission_ids)
        project_data = yield self._get_permission_detail(fields='id, name', table='project', params=project_ids)
        filehub_data = yield self._get_permission_detail(fields='id, filename', table='filehub', params=filehub_ids)

        server_data = yield self.fetch_instance_info(server_ids)

        data = self.merge_dict_samekey(server_data)
        self.log.info(list(data.items()))

        self.log.info(permission_data)
        self.log.info(project_data)
        self.log.info(filehub_data)
        # self.log.info(server_data)

    @coroutine
    def _get_permission_detail(self, fields, table, params):
        sql = """
                SELECT {field} from {table} WHERE id in %s
              """.format(field=fields, table=table)
        cur = yield self.db.execute(sql, [params])
        return cur.fetchall()

    @coroutine
    def fetch_instance_info(self, server_ids):
        sql = " SELECT i.provider, i.region_name, s.id as sid, s.name FROM instance i JOIN server s USING(instance_id) WHERE s.id in %s"
        cur = yield self.db.execute(sql, server_ids)
        info = cur.fetchall()
        return info

    def merge_dict_samekey(self, data):
        result = defaultdict(dict)

        for d in data:
            provider, region = d['provider'], d['region_name']

            if region not in result[provider]:
                result[provider][region] = []

            result[provider][region].append({'sid': d['sid'], 'name': d['name']})
        return result
