__author__ = 'Jon'

import json
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor

from service.base import BaseService
from utils.ssh import SSH
from constant import CMD_MONITOR


class ServerService(BaseService):
    table = 'server'
    fields = 'id, name, address, ip, machine_status, business_status'

    @coroutine
    def save_report(self, params):
        """ 保存主机上报的信息
        """
        cpu = json.dumps(params['mem'])
        mem = json.dumps(params['mem'])
        disk = json.dumps(params['disk'])
        post_time = params['time']['time']

        data = [params.get('server_id', 0), params.get('cluster_id', 0), post_time]
        sql = "INSERT INTO %s(cluster_id, server_id, created_time,content)"
        suffix = "values(%s,%s,%s,%s)"

        cpu_sql = sql % ("cpu") + suffix
        cpu_data = data + [cpu]
        self.log.info(cpu_sql)
        self.log.info(cpu_data)
        yield self.db.execute(cpu_sql, cpu_data)

        mem_sql = sql % ("memory") + suffix
        mem_data = data + [mem]
        self.log.info(mem_sql)
        self.log.info(mem_data)
        yield self.db.execute(mem_sql, mem_data)

        disk_sql = sql % ("disk") + suffix
        disk_data = data + [disk]
        self.log.info(disk_sql)
        self.log.info(disk_data)
        yield self.db.execute(disk_sql, disk_data)

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
