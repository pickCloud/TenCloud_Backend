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

        permission_ids = '({ids})'.format(ids=id_data['permissions'])
        project_ids = '({ids})'.format(ids=id_data['access_projects'])
        server_ids = '({ids})'.format(ids=id_data['access_servers'])
        filehub_ids = '({ids})'.format(ids=id_data['access_filehub'])

        permission_data = yield self._get_permission_detail(fields='id, name, `group`', table='permission', params=permission_ids)
        project_data = yield self._get_permission_detail(fields='id, name', table='project', params=project_ids)
        filehub_data = yield self._get_permission_detail(fields='id, filename', table='filehub', params=filehub_ids, extra='type=1 AND')

        server_data = yield self.fetch_instance_info(server_ids)
        server_data = yield self.merge_dict_samekey(server_data)

        data = {
            'permission': permission_data,
            'servers': dict(server_data.items()),
            'projects': project_data,
            'filehub': filehub_data
        }
        return data

    @coroutine
    def _get_permission_detail(self, fields, table, params, extra=''):
        sql = """
                SELECT {field} from {table} WHERE {extra} id in {params}
              """.format(field=fields, table=table, params=params, extra=extra)
        cur = yield self.db.execute(sql)
        return cur.fetchall()

    @coroutine
    def fetch_instance_info(self, server_ids):
        sql = """
                SELECT i.provider, i.region_name, s.id as sid, s.name FROM instance i JOIN server s USING(instance_id) WHERE s.id in {ids}
              """.format(ids=server_ids)
        cur = yield self.db.execute(sql)
        info = cur.fetchall()
        return info

    @coroutine
    def merge_dict_samekey(self, data):
        result = defaultdict(dict)

        for d in data:
            provider, region = d['provider'], d['region_name']

            if region not in result[provider]:
                result[provider][region] = []

            result[provider][region].append({'sid': d['sid'], 'name': d['name']})
        return result
