__author__ = 'Jon'

import json
import paramiko
from tornado.gen import coroutine, Task
from tornado.concurrent import run_on_executor

from service.base import BaseService
from constant import DEPLOYING, DEPLOYED


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
        ssh = paramiko.SSHClient()
        paramiko.util.log_to_file('logs/sysdeploy.log')
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=params['ip'], port=22, username=params['username'], password=params['passwd'])
        stdin, stdout, stderr = ssh.exec_command('curl -sSL http://47.94.18.22/supermonitor/install.sh | sh')
        result = stdout.read()
        ssh.close()

    @coroutine
    def save_server_account(self, params):
        sql = " INSERT INTO server_account(ip, username, passwd) "\
              " VALUES(%s, %s, %s)"

        yield self.db.execute(sql, [params['ip'], params['username'], params['passwd']])