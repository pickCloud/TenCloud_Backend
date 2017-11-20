from tornado.gen import coroutine

from service.permission.permission_base import PermissionBaseService


class PermissionTemplateService(PermissionBaseService):
    table = 'permission_template'
    fields = """
            id, name, cid, permissions, access_servers, access_projects,
            access_projects, access_filehub
            """

    @coroutine
    def get_template_permission(self, id):
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

        permission_data = yield self._get_template_permission(fields='id, name, `group`', table='permission', params=permission_ids)
        project_data = yield self._get_template_permission(fields='id, name', table='project', params=project_ids)
        filehub_data = yield self._get_template_permission(fields='id, filename', table='filehub', params=filehub_ids, extra='type=1 AND')

        server_data = yield self.fetch_instance_info(server_ids)
        server_data = yield self.merge_dict(server_data)

        data = {
            'permission': permission_data,
            'servers': server_data,
            'projects': project_data,
            'filehub': filehub_data
        }
        return data

    @coroutine
    def _get_template_permission(self, fields, table, params, extra=''):
        sql = """
                SELECT {field} from {table} WHERE {extra} id in {params}
              """.format(field=fields, table=table, params=params, extra=extra)
        cur = yield self.db.execute(sql)
        return cur.fetchall()


