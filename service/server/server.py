__author__ = 'Jon'

import json
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor

from service.base import BaseService
from utils.ssh import SSH
from constant import CMD_MONITOR


class ServerService(BaseService):
    table  = 'server'
    fields = 'id, name, address, ip, machine_status, business_status'

    @coroutine
    def save_report(self, params):
        ''' 保存主机上报的信息
        '''
        performance = [json.dumps(params[i]) for i in ['cpu', 'mem', 'disk']]

        data = [params.get('name', ''), params.get('cluster_id', 0), params['ip']] + performance*2

        sql = " INSERT INTO server(name, cluster_id, ip, cpu, memory, disk) "\
              " VALUES(%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE "\
              " name=name, cluster_id=cluster_id, cpu=%s, memory=%s, disk=%s"

        yield self.db.execute(sql, data)

    @run_on_executor
    def remote_deploy(self, params):
        ''' 远程部署主机
        '''
        ssh = SSH(hostname=params['ip'], username=params['username'], passwd=params['passwd'])
        ssh.exec(CMD_MONITOR)
        ssh.close()

    @coroutine
    def save_server_account(self, params):
        sql = " INSERT INTO server_account(ip, username, passwd) "\
              " VALUES(%s, %s, %s)"

        yield self.db.execute(sql, [params['ip'], params['username'], params['passwd']])