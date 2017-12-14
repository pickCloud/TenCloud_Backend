from tornado.gen import coroutine

from service.permission.permission_base import PermissionBaseService

class PermissionService(PermissionBaseService):
    table = 'permission'
    fields = 'id, name, group'

    @coroutine
    def get_user_permission(self, cid,uid):
        arg = [uid, cid]

        permission_data = yield self._get_user_permission(
                                                    fields='a.id, a.name, `group`',
                                                    table='permission',
                                                    where_fields='a.id=b.pid',
                                                    where_table='user_permission',
                                                    params=arg
        )
        permission_data = yield self.merge_permissions(permission_data)

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
        ids = ','.join(ids)
        server_data = yield self.fetch_instance_info(extra='WHERE s.id in ({ids})'.format(ids=ids))
        server_data = yield self.merge_servers(server_data)

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
