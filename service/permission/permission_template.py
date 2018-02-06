from tornado.gen import coroutine

from service.permission.permission_base import PermissionBaseService
from constant import PT_FORMAT, RESOURCE_TYPE


class PermissionTemplateService(PermissionBaseService):
    table = 'permission_template'
    fields = """
            id, name, cid, permissions, access_servers, access_projects, access_filehub, type
            """

    @coroutine
    def get_template_permission(self, params):
        source_id_sql = """
                        SELECT name, permissions, access_servers, access_projects, access_filehub
                        FROM permission_template WHERE id=%s LIMIT 1
                        """
        cur = yield self.db.execute(source_id_sql, [params['id']])
        id_data = cur.fetchone()

        if not id_data:
            raise ValueError('id不存在')

        permission_data = []
        server_data = []
        project_data = []
        filehub_data = []

        if id_data.get('access_projects', ''):
            project_ids = '({ids})'.format(ids=id_data['access_projects'])
            project_data = yield self._get_template_permission(fields='id, name', table='project', params=project_ids)

        if id_data.get('access_filehub', ''):
            filehub_ids = '({ids})'.format(ids=id_data['access_filehub'])
            filehub_data = yield self._get_template_permission(fields='id, filename', table='filehub', params=filehub_ids, extra='type=1 AND')

        if id_data.get('permissions', ''):
            permission_ids = '({ids})'.format(ids=id_data['permissions'])
            permission_data = yield self._get_template_permission(fields='id, name, `group`', table='permission', params=permission_ids, extra='is_show=1 AND')

        if id_data.get('access_servers', ''):
            server_ids = '({ids})'.format(ids=id_data['access_servers'])
            server_data = yield self.fetch_instance_info(extra='WHERE s.id in {ids}'.format(ids=server_ids))

        if params['format'] == PT_FORMAT['simple']:
            data = {
                'name': id_data['name'],
                'permissions': permission_data,
                'access_servers': server_data,
                'access_projects': project_data,
                'access_filehub': filehub_data
            }
            return data

        permissions_data = self.merge_permissions(permission_data)
        server_data = self.merge_servers(server_data)

        data = {
            'name': id_data['name'],
            'data': [
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
        }
        return data

    @coroutine
    def _get_template_permission(self, fields, table, params, extra=''):
        sql = """
                SELECT {field} from {table} WHERE {extra} id in {params}
              """.format(field=fields, table=table, params=params, extra=extra)
        cur = yield self.db.execute(sql)
        return cur.fetchall()

    @coroutine
    def get_resources(self, cid, is_format = False):
        # 暂时获取所有资源
        files = yield self._get_resources(
                                        fields='id, filename, type',
                                        table='filehub',
                                        extra='where lord={cid} and form = {form}'.format(cid=cid, form=RESOURCE_TYPE['firm'])
                                        )
        projects = yield self._get_resources(
                                        fields='id, name',
                                        table='project',
                                        extra='where lord={cid} and form = {form}'.format(cid=cid, form=RESOURCE_TYPE['firm'])
                                        )

        permissions = yield self._get_resources(fields='id, name, `group`', table='permission', extra='where is_show=1')
        servers = yield self.fetch_instance_info(extra='where s.lord={cid} and s.form={form}'.format(cid=cid, form=RESOURCE_TYPE['firm']))

        if is_format:
            data = {
                'files': files if files else [],
                'projects': projects if projects else [],
                'permissions': permissions if permissions else [],
                'servers': servers if servers else []
            }
            return data

        permissions = self.merge_permissions(permissions)
        servers = self.merge_servers(servers)

        data = [
            {
                'name': '功能',
                'data': permissions
            },
            {
                'name': '数据',
                'data': [
                    {
                        'name': '文件仓库',
                        'data': [
                            {'name': '文件仓库', 'data': files if files else []}
                        ]
                    },
                    {
                        'name': '项目管理',
                        'data': [
                            {'name': '项目管理', 'data': projects if projects else []}
                        ]
                    },
                    {
                        'name': '云服务器',
                        'data': servers if servers else []
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

    @coroutine
    def get_admin(self, cid):
        data = yield self.get_resources(cid=cid, is_format=True)
        permissions = ','.join([str(i['id']) for i in data['permissions']])
        servers = ','.join([str(i['sid']) for i in data['servers']])
        files = ','.join([str(i['id']) for i in data['files']])
        projects = ','.join([str(i['id']) for i in data['projects']])
        data = {
            'name': '所有权限',
            'cid': cid,
            'permissions': permissions,
            'access_servers': servers,
            'access_filehub': files,
            'access_projects': projects,
            'create_time': '',
            'update_time': '',
            'type': 0
        }
        return data

    @coroutine
    def check_pt_exist(self, pts):
        data = []
        for pt in pts:
            tmp_data = yield self._check_pt_exist(pt)
            data.append(tmp_data)
        return data

    @coroutine
    def _check_pt_exist(self, data):
        self.log.info(data)
        servers = yield self.check_exist(table='server', ids=data['access_servers'])
        projects = yield self.check_exist(table='project', ids=data['access_projects'])
        files = yield self.check_exist(table='filehub', ids=data['access_filehub'])
        permission = yield self.check_exist(table='permission', ids=data['permissions'])
        data['access_servers'] = servers
        data['access_projects'] = projects
        data['access_filehub'] = files
        data['permissions'] = permission
        return data