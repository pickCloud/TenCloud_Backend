

from tornado.gen import coroutine
from constant import FULL_DATE_FORMAT, OPERATION_OBJECT_STYPE
from service.base import BaseService


class ServerOperationService(BaseService):
    table = 'operation_log'
    fields = 'id, object_id, user_id, operation, operation_status, object_type'

    @coroutine
    def get_server_operation(self, server_id):
        sql = """
                SELECT DATE_FORMAT(s.created_time, %s) AS created_time, 
                    s.operation AS operation, 
                    s.operation_status AS operation_status,
                    u.name AS user
                FROM operation_log s
                JOIN user u on s.user_id=u.id
                WHERE s.object_type=%s AND s.object_id=%s
              """

        cur = yield self.db.execute(sql, [FULL_DATE_FORMAT, OPERATION_OBJECT_STYPE['server'], server_id])
        return cur.fetchall()
