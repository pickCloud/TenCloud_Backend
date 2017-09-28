

from tornado.gen import coroutine
from constant import FULL_DATE_FORMAT
from service.base import BaseService


class ServerOperationService(BaseService):
    table = 'server_operation'
    fields = 'id, public_ip, user_id, operation'

    @coroutine
    def get_server_operation(self, public_ip):
        sql = """
                SELECT DATE_FORMAT(s.created_time, %s) AS created_time, 
                    s.operation AS operation, 
                    u.name AS user, 
                    i.status AS machine_status
                FROM server_operation s
                JOIN instance i on s.public_ip=i.public_ip
                JOIN user u on s.user_id=u.id
                WHERE s.public_ip=%s
              """
        cur = yield self.db.execute(sql, [FULL_DATE_FORMAT, public_ip])
        return cur.fetchall()
