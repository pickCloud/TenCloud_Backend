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

        return data

    @coroutine
    def save_report(self, params):
        performance = [json.dumps(params[i]) for i in ['cpu', 'mem', 'disk']]

        data = [params.get('name', ''), params.get('cluster_id', 0), params['ip']] + performance*2

        sql = " INSERT INTO server(name, cluster_id, ip, cpu, memory, disk) "\
              " VALUES(%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE "\
              " name=name, cluster_id=cluster_id, cpu=%s, memory=%s, disk=%s"

        yield self.db.execute(sql, data)

    @coroutine
    def to_feedback(self, token):
        yield Task(self.redis.hset, SERVER_TOKEN, token, TOKEN_FLAG)