from tornado.gen import coroutine

from service.permission.permission_base import PermissionBaseService
from constant import PT_FORMAT, RIGHT, ERR_TIP
from utils.error import AppError

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
                                                    params=arg,
                                                    extra='and a.is_show=1'
        )
        project_data = yield self._get_user_permission(
                                                    fields='a.id, a.name',
                                                    table='project',
                                                    where_fields='a.id=b.pid',
                                                    where_table='user_access_project',
                                                    params=arg
        )
        filehub_data = yield self._get_user_permission(
                                                    fields='a.id, a.filename, a.type, a.mime',
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
        server_data = []
        if ids:
            ids = ','.join(ids)
            server_data = yield self.fetch_instance_info(extra='WHERE s.id in ({ids})'.format(ids=ids))

        if params['format'] == PT_FORMAT['simple']:
            data = {
                'permissions': permission_data,
                'access_servers': server_data,
                'access_projects': project_data,
                'access_filehub': filehub_data,
            }
            return data

        server_data = self.merge_servers(server_data)
        permission_data = self.merge_permissions(permission_data)
        data = [
            {
                'name': '功能',
                'data': permission_data
            },
            {
                'name': '数据',
                'data': [
                    {
                        'name': '文件仓库',
                        'data': [
                            {'name': '文件仓库', 'data': filehub_data}
                        ]
                    },
                    {
                        'name': '项目管理',
                        'data': [
                            {'name': '项目管理', 'data': project_data}
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
    def _get_user_permission(self, fields, table, where_fields, where_table, params, extra=''):
        sql = """
                SELECT {fields} FROM {table} AS a JOIN {where_table} AS b 
                ON {where_fields} WHERE b.uid=%s AND b.cid=%s {extra}
              """.format(
                        fields=fields, table=table,
                        where_fields=where_fields, where_table=where_table,
                        extra=extra
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

        if  params.get('data'):
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
            # 个人不需要检查
            if not params.get('cid'): return

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

    @coroutine
    def get_user_by_permission(self, cid, pid):
        '''
        获取公司中具有某种权限的员工
        :param cid:
        :param pid:
        :return: [1,2,3] 员工列表
        '''
        user = yield self.select(fields='uid', conds={'cid': cid, 'pid': pid}, ct=False, ut=False)

        user_list = [u['uid'] for u in user]
        return user_list

    @coroutine
    def filter_id_card_info(self, info, cid, uid):
        '''
        检查员工是否具有某种权限
        :param info:
        :param cid:
        :param uid:
        :return:
        '''

        p = yield self.select(conds={'cid': cid, 'uid': uid, 'pid': RIGHT['view_employee_id_info']}, one=True)
        if not p:
            for i in info:
                if i['uid'] == uid:
                    continue
                i.pop('id_card', None)

        return info

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

        if key == 'dir':
            # 如果是文件的过滤动作，需要比较目标数据是否为权限目录的子串
            return [i for i in data for j in limits if str(j) in i[key]]
        else:
            return [i for i in data if i[key] in limits]


class UserAccessServerService(UserAccessBaseService):
    table = 'user_access_server'
    fields = 'id, uid, sid, cid'
    resource = 'sid'


class UserAccessProjectService(UserAccessBaseService):
    table = 'user_access_project'
    fields = 'id, uid, pid, cid'
    resource = 'pid'

class UserAccessApplicationService(UserAccessBaseService):
    table = 'user_access_application'
    fields = 'id, uid, aid, cid'
    resource = 'aid'

class UserAccessFilehubService(UserAccessBaseService):
    table = 'user_access_filehub'
    fields = 'id, uid, fid, cid'
    resource = 'fid'

    @coroutine
    def check_right(self, params):
        '''
        检查用户是否有操作指定文件的数据权限
        :param params: {'uid', 'cid', 'ids'}
        :return: 如果权限不够，raise
        '''

        ids = params.get('ids')
        if ids:
            file_id = ','.join(str(i) for i in list(ids))
        else:
            return

        # 获取需要操作的文件完整路径
        sql = """
            SELECT dir FROM filehub WHERE id in ({file_id})
            """.format(file_id=file_id)
        cur = yield self.db.execute(sql)
        data = cur.fetchall()

        # 获取当前用户具有操作权限的目录完整路径
        pdata = yield self.get_by_permission(fields='dir',
                                             table='filehub',
                                             where_fields='a.id=b.fid',
                                             where_table=self.table,
                                             params=[params['uid'], params['cid']])

        # 遍历所有用户需要操作的文件，若其在用户权限目录范围内则为合法，否则直接不允许用户操作
        self.issubdir(data, pdata)

    def issubdir(self, data, pdata):
        '''
        检查用户需要访问的数据是否为权限数据的子集
        :param data: [str, str, ... str]
        :param pdata: [str, str, ... str]
        :return:
        '''
        for i in data:
            result = True
            for j in pdata:
                if j['dir'] in i['dir']:
                    result = False
                    break
            if result:
                raise AppError(ERR_TIP['no_permission']['msg'], ERR_TIP['no_permission']['sts'])
