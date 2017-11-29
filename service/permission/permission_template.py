from tornado.gen import coroutine

from service.permission.permission_base import PermissionBaseService


class PermissionTemplateService(PermissionBaseService):
    table = 'permission_template'
    fields = """
            id, name, cid, permissions, access_servers, access_projects, access_filehub
            """

    @coroutine
    def get_template_permission(self, id):
        source_id_sql = """
                        SELECT permissions, access_servers, access_projects, access_filehub
                        FROM permission_template WHERE id=%s LIMIT 1
                        """
        cur = yield self.db.execute(source_id_sql, [id])
        id_data = cur.fetchone()

        if not id_data:
            raise ValueError('id不存在')

        permission_ids = '({ids})'.format(ids=id_data['permissions'])
        project_ids = '({ids})'.format(ids=id_data['access_projects'])
        server_ids = '({ids})'.format(ids=id_data['access_servers'])
        filehub_ids = '({ids})'.format(ids=id_data['access_filehub'])

        permission_data = yield self._get_template_permission(fields='id, name, `group`', table='permission', params=permission_ids)
        permissions_data = yield self.merge_list(permission_data)

        project_data = yield self._get_template_permission(fields='id, name', table='project', params=project_ids)
        filehub_data = yield self._get_template_permission(fields='id, filename', table='filehub', params=filehub_ids, extra='type=1 AND')

        server_data = yield self.fetch_instance_info(extra='WHERE s.id in {ids}'.format(ids=server_ids))
        server_data = yield self.merge_dict(server_data)

        data = [
            {
                'name': 'functions',
                'categories': permissions_data
            },
            {
                'name': 'data',
                'categories': [
                    {
                        'name': 'filehub',
                        'data': filehub_data
                    },
                    {
                        'name': 'project',
                        'data': project_data
                    },
                    {
                        'name': 'server',
                        'data': server_data
                    }
                ]
            }
        ]
        return data

    @coroutine
    def _get_template_permission(self, fields, table, params, extra=''):
        sql = """
                SELECT {field} from {table} WHERE {extra} id in {params}
              """.format(field=fields, table=table, params=params, extra=extra)
        cur = yield self.db.execute(sql)
        return cur.fetchall()

    @coroutine
    def get_resources(self, cid):
        # 暂时获取所有资源
        files = yield self._get_resources(fields='id, filename', table='filehub', extra='where cid={cid} and type=1'.format(cid=cid))
        projects = yield self._get_resources(fields='id, name', table='project', extra='where cid={cid}'.format(cid=cid))

        permissions = yield self._get_resources(fields='id, name, `group`', table='permission')
        permissions = yield self.merge_list(permissions)

        servers = yield self.fetch_instance_info()
        servers = yield self.merge_dict(servers)
        data = [
            {
                'name': 'functions',
                'categories': permissions
            },
            {
                'name': 'data',
                'categories': [
                    {
                        'name': 'filehub',
                        'data': files
                    },
                    {
                        'name': 'project',
                        'data': projects
                    },
                    {
                        'name': 'server',
                        'data': servers
                    }
                ]
            }
        ]
        return data

    @coroutine
    def _get_resources(self, fields, table, extra=''):

        sql = """
            SELECT {fields} FROM {table} {extra}
              """.format(fields=fields, table=table,extra=extra)
        cur = yield self.db.execute(sql)
        data = cur.fetchall()
        return data
