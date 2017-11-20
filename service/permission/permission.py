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
        ids = ','.join([str(i['sid']) for i in cur.fetchall()])
        server_ids = '({ids})'.format(ids=ids)
        server_data = yield self.fetch_instance_info(server_ids)
        server_data = yield self.merge_dict(server_data)

        data = {
            'permission': permission_data,
            'servers': server_data,
            'projects': project_data,
            'filehub': filehub_data,
        }
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
    def update_user_access_server(self, params):
        table = 'user_access_server'
        set_fields='sid={sid}'.format(sid=params['server_id'])
        self.log.info(set_fields)
        yield self._delete_and_insert(
                                            table=table,
                                            set_fields=set_fields,
                                            params=params
        )

    @coroutine
    def update_user_access_project(self, params):
        table = 'user_access_project'
        set_fields='pid={pid}'.format(pid=params['project_id'])
        yield self._delete_and_insert(
                                            table=table,
                                            set_fields=set_fields,
                                            params=params
        )

    @coroutine
    def update_user_access_filehub(self, params):
        table = 'user_access_filehub'
        set_fields='fid={fid}'.format(fid=params['filehub_id'])
        yield self._delete_and_insert(
                                            table=table,
                                            set_fields=set_fields,
                                            params=params
        )

    @coroutine
    def update_user_permission(self, params):
        table = 'user_permission'
        set_fields='pid={pid}'.format(pid=params['permission_id'])
        yield self._delete_and_insert(
                                            table=table,
                                            set_fields=set_fields,
                                            params=params
        )

    @coroutine
    def _delete_and_insert(self, table, set_fields, params):
        sql = """
            DELETE FROM {table} WHERE cid={cid} AND uid={uid}
            """.format(table=table, cid=params['cid'], uid=params['uid'])

        yield self.db.execute(sql)

        sql = """
                INSERT INTO {table} SET {set_fields}, uid={uid}, cid={cid}
            """.format(
                        table=table, set_fields=set_fields,
                        uid=params['uid'], cid=params['cid']
                        )

        yield self.db.execute(sql)
