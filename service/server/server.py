__author__ = 'Jon'

import json
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor

from service.base import BaseService
from utils.ssh import SSH
from constant import CMD_MONITOR


class ServerService(BaseService):
    # table = 'server'
    # fields = 'id, name, address, ip, machine_status, business_status'

    @coroutine
    def save_report(self, params):
        """ 保存主机上报的信息
        """
        base_data = [params['public_ip'], params['time']]
        base_sql = 'INSERT INTO %s(public_ip, created_time,content)'
        suffix = ' values(%s,%s,%s)'
        for table in ['cpu', 'memory', 'disk']:
            content = json.dumps(params[table])
            sql = (base_sql % table) + suffix
            yield self.db.execute(sql, base_data + [content])

    @run_on_executor
    def remote_deploy(self, params):
        """ 远程部署主机
        """
        ssh = SSH(hostname=params['ip'], username=params['username'], passwd=params['passwd'])
        ssh.exec(CMD_MONITOR)
        ssh.close()

    @coroutine
    def save_server_account(self, params):
        sql = " INSERT INTO server_account(ip, username, passwd) " \
              " VALUES(%s, %s, %s)"

        yield self.db.execute(sql, [params['ip'], params['username'], params['passwd']])
