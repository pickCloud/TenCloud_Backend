__author__ = 'Jon'

import json
from tornado.gen import coroutine
from service.base import BaseService


class ServerService(BaseService):
    table  = 'server'
    fields = 'id, name, address, ip, machine_status, business_status'

    @coroutine
    def save_report(self, params):
        ip = params['ip']
        performance = [json.dumps(params[i]) for i in ['cpu', 'mem', 'disk']]

        sql = " INSERT INTO server(ip, cpu, memory, disk) "\
              " VALUES(%s, %s, %s, %s) ON DUPLICATE KEY UPDATE "\
              " cpu=%s, memory=%s, disk=%s"

        yield self.db.execute(sql, [ip] + performance*2)