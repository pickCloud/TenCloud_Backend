from tornado.gen import coroutine

from service.permission.permission_base import PermissionBaseService
from constant import PT_FORMAT

#######################################################################################################################
# 功能权限
#######################################################################################################################
class PermissionService(PermissionBaseService):
    table = 'permission'
    fields = 'id, name, group'

    @coroutine
    def get_user_permission(self, params):
        arg = [params['uid'], params['cid']]
        permission_data = yield self._get_user_permission(
                                                    fields='a.id, a.name, `group`',
                                                    table='permission',
                                                    where_fields='a.id=b.pid',
                                                    where_table='user_permission',
                                                    params=arg
        )
        project_data = yield self._get_user_permission(
                                                    fields='a.id, a.name',
                                                    table='project',
                                                    where_fields='a.id=b.pid',
                                                    where_table='user_access_project',
                                                    params=arg
        )
        filehub_data = yield self._get_user_permission(
                                                    fields='a.id, a.filename',
                                                    table='filehub',
                                                    where_fields='a.id=b.fid',
                                                    where_table='user_access_filehub',
                                                    params=arg
        )

        sql = """
                SELECT sid FROM user_access_server WHERE uid=%s AND cid=%s 
              """
        cur = yield self.db.execute(sql, arg)
        ids = [str(i['sid']) for i in cur.fetchall()]
        server_data = ''
        if ids:
            ids = ','.join(ids)
            server_data = yield self.fetch_instance_info(extra='WHERE s.id in ({ids})'.format(ids=ids))

        if params['format'] == PT_FORMAT:
            data = {
                'permissions': permission_data,
                'access_servers': server_data,
                'access_projects': project_data,
                'access_filehub': filehub_data,
            }
            return data

        server_data = yield self.merge_servers(server_data)
        permission_data = yield self.merge_permissions(permission_data)
        data = [
            {
                'name': '功能',
                'data': permission_data
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
    def _get_user_permission(self, fields, table, where_fields, where_table, params):
        sql = """
                SELECT {fields} FROM {table} AS a JOIN {where_table} AS b 
                ON {where_fields} WHERE b.uid=%s AND b.cid=%s
              """.format(
                        fields=fields, table=table,
                        where_fields=where_fields, where_table=where_table
                        )
        cur = yield self.db.execute(sql, params)
        data = cur.fetchall()
        return data

    @coroutine
    def update_user(self, params):
        sql = """
            DELETE FROM {table} WHERE cid={cid} AND uid={uid}
            """.format(table=params['table'], cid=params['cid'], uid=params['uid'])

        yield self.db.execute(sql)

        sql = """
                INSERT INTO {table} {fields} VALUES {values}
            """.format(table=params['table'], fields=params['fields'], values=params['data'])

        yield self.db.execute(sql)


class UserPermissionService(PermissionBaseService):
    table = 'user_permission'
    fields = 'id, uid, pid, cid'
    resource = 'pid'

    def ws_check_permission(self, params):
        ''' WebSocket查看权限，因为WebSocket的open并不支持异步
        :param params: {'uid', 'cid', 'pids'}
        :return:
        '''
        cursor = self.sync_db.cursor()
        try:
            # 管理员不需要检查
            sql = '''
                SELECT * FROM company_employee WHERE uid=%s AND cid=%s AND is_admin=%s
            '''
            cursor.execute(sql, [params['uid'], params['cid'], 1])
            result = cursor.fetchone()
            if result: return

            # 检查权限
            sql = '''
                SELECT pid FROM user_permission WHERE uid=%s AND cid=%s
            '''
            cursor.execute(sql, [params['uid'], params['cid']])
            result = cursor.fetchall()
            self.issub(params.get('pids'), result)
        finally:
            cursor.close()



#######################################################################################################################
# 数据权限
#######################################################################################################################
class UserAccessBaseService(PermissionBaseService):
    @coroutine
    def filter(self, data, uid, cid, key='id'):
        ''' 过滤用户不可见数据
        :param params: {'data', 'uid', 'cid', 'key'(哪个键对应数据库字段)}
        '''
        db_data = yield self.select(fields=self.resource, conds={'uid': uid, 'cid': cid})

        limits = [i[self.resource] for i in db_data]

        return [i for i in data if i[key] in limits]


class UserAccessServerService(UserAccessBaseService):
    table = 'user_access_server'
    fields = 'id, uid, sid, cid'
    resource = 'sid'