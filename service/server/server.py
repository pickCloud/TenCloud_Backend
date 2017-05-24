__author__ = 'Jon'

import json
from tornado.gen import coroutine, Task
from service.base import BaseService
from constant import SERVER_TOKEN, TOKEN_FLAG


class ServerService(BaseService):
    table  = 'server'
    fields = 'id, name, address, ip, machine_status, business_status'

    @coroutine
    def check_token(self, token):
        data = yield Task(self.redis.hget, SERVER_TOKEN, token)

        if not data:
            raise ValueError('token miss')

        return data == TOKEN_FLAG

    @coroutine
    def save_report(self, params):
        ip = params['ip']
        performance = [json.dumps(params[i]) for i in ['cpu', 'mem', 'disk']]

        sql = " INSERT INTO server(ip, cpu, memory, disk) "\
              " VALUES(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE "\
              " cpu=%s, memory=%s, disk=%s"

        yield self.db.execute(sql, [ip] + performance*2)

    @coroutine
    def to_feedback(self, token):
        yield Task(self.redis.hset, SERVER_TOKEN, token, TOKEN_FLAG)