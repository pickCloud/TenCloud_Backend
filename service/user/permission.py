from collections import defaultdict

from service.base import BaseService
from tornado.gen import coroutine


class PermissionService(BaseService):
    table = 'permission'
    fields = 'id, name, group'

    @coroutine
    def get_user_permission(self, params):
        arg = [params['uid'], params['cid']]

        permission_data = yield self._get_more_info(
                                                    fields='id, name, `group`',
                                                    table='permission',
                                                    where_fields='pid',
                                                    where_table='user_permission',
                                                    params=arg
        )
        project_data = yield self._get_more_info(
                                                    fields='id, name',
                                                    table='project',
                                                    where_fields='pid',
                                                    where_table='user_access_project',
                                                    params=arg
        )
        filehub_data = yield self._get_more_info(
                                                    fields='id, filename',
                                                    table='filehub',
                                                    where_fields='fid',
                                                    where_table='user_access_filehub',
                                                    params=arg
        )

        sql = """
                SELECT sid FROM user_access_server WHERE uid=%s AND cid=%s 
              """
        cur = yield self.db.execute(sql, arg)
        ids = ','.join([str(i['sid']) for i in cur.fetchall()])
        server_ids = '({ids})'.format(ids=ids)
        server_data = yield self.fetch_instance_info(server_ids)
        server_data = yield self.merge_dict_samekey(server_data)

        data = {
            'permission': permission_data,
            'servers': dict(server_data.items()),
            'projects': project_data,
            'filehub': filehub_data,
        }
        return data

    @coroutine
    def _get_more_info(self, fields, table, where_fields, where_table, params):
        sql = """
                SELECT {fields} FROM {table} WHERE id IN 
                  (SELECT {where_fields} FROM {where_table} WHERE uid=%s AND cid=%s)
              """.format(
                        fields=fields, table=table,
                        where_fields=where_fields, where_table=where_table
                        )
        cur = yield self.db.execute(sql, params)
        data = cur.fetchall()
        return data

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

