__author__ = 'Jon'

import json
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor

from service.base import BaseService
from utils.ssh import SSH
from constant import CMD_MONITOR


class ServerService(BaseService):
    def __init__(self):
        super().__init__()
        self.base_data = []
        self.base_sql = ""
        self.suffix = ""
    # table = 'server'
    # fields = 'id, name, address, ip, machine_status, business_status'

    @coroutine
    def save(self, table, content):
        base_data = self.base_data[:]
        base_data.append(content)
        sql = (self.base_sql % table) + self.suffix
        yield self.db.execute(sql, base_data)

    @coroutine
    def save_report(self, params):
        """ 保存主机上报的信息
        """
        cpu = json.dumps(params['cpu'])
        mem = json.dumps(params['mem'])
        disk = json.dumps(params['disk'])
        post_time = params['time']

        self.base_data = [params.get('server_id', 0), params.get('cluster_id', 0), post_time]
        self.base_sql = 'INSERT INTO %s(cluster_id, server_id, created_time,content)'
        self.suffix = ' values(%s,%s,%s,%s)'

        self.save(table='cpu', content=cpu)
        self.save(table='memory', content=mem)
        self.save(table='disk', content=disk)

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
