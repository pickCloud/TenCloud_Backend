from tornado.gen import coroutine

from service.permission.permission_base import PermissionBaseService
from constant import  PT_FORMAT

class PermissionTemplateService(PermissionBaseService):
    table = 'permission_template'
    fields = """
            id, name, cid, permissions, access_servers, access_projects, access_filehub
            """

    @coroutine
    def get_template_permission(self, params):
        source_id_sql = """
                        SELECT permissions, access_servers, access_projects, access_filehub
                        FROM permission_template WHERE id=%s LIMIT 1
                        """
        cur = yield self.db.execute(source_id_sql, [params['id']])
        id_data = cur.fetchone()

        if not id_data:
            raise ValueError('id不存在')

        permission_ids = '({ids})'.format(ids=id_data['permissions'])
        project_ids = '({ids})'.format(ids=id_data['access_projects'])
        server_ids = '({ids})'.format(ids=id_data['access_servers'])
        filehub_ids = '({ids})'.format(ids=id_data['access_filehub'])

        permission_data = ''
        server_data = ''
        project_data = ''
        filehub_data = ''

        if project_ids:
            project_data = yield self._get_template_permission(fields='id, name', table='project', params=project_ids)

        if filehub_ids:
            filehub_data = yield self._get_template_permission(fields='id, filename', table='filehub', params=filehub_ids, extra='type=1 AND')

        if permission_ids:
            permission_data = yield self._get_template_permission(fields='id, name, `group`', table='permission', params=permission_ids)

        if server_ids:
            server_data = yield self.fetch_instance_info(extra='WHERE s.id in {ids}'.format(ids=server_ids))

        if params['format'] == PT_FORMAT:
            data = {
                'permissions': permission_data,
                'access_servers': server_data,
                'access_projects': project_data,
                'access_filehub': filehub_data
            }
            return data

        permissions_data = yield self.merge_permissions(permission_data)
        server_data = yield self.merge_servers(server_data)

        data = [
            {
                'name': '功能',
                'data': permissions_data
            },
            {
                'name': '数据',
                'data': [
                    {
                        'name': '文件',
                        'data': [
                            {'name': '文件', 'data': filehub_data}
                        ]
                    },
                    {
                        'name': '项目',
                        'data': [
                            {'name': '项目', 'data': project_data}
                        ]
                    },
                    {
                        'name': '云服务器',
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
        permissions = yield self.merge_permissions(permissions)

        servers = yield self.fetch_instance_info()
        servers = yield self.merge_servers(servers)
        data = [
            {
                'name': '功能',
                'data': permissions
            },
            {
                'name': '数据',
                'data': [
                    {
                        'name': '文件',
                        'data': [
                            {'name': '文件', 'data': files}
                        ]
                    },
                    {
                        'name': '项目',
                        'data': [
                            {'name': '项目', 'data': projects}
                        ]
                    },
                    {
                        'name': '云服务器',
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
