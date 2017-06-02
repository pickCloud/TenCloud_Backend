__author__ = 'Jon'

import json
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor

from service.base import BaseService
from utils.ssh import SSH
from utils.general import get_in_format
from utils.aliyun import Aliyun
from constant import CMD_MONITOR, INSTANCE_STATUS


class ServerService(BaseService):
    table  = 'server'
    fields = 'id, name, public_ip, business_status, cluster_id'

    @coroutine
    def save_report(self, params):
        ''' 保存主机上报的信息
        '''
        performance = [json.dumps(params[i]) for i in ['cpu', 'mem', 'disk']]

        data = [params.get('name', ''), params.get('cluster_id', 0), params['public_ip']] + performance*2

        sql = " INSERT INTO server(name, cluster_id, public_ip, cpu, memory, disk) "\
              " VALUES(%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE "\
              " name=name, cluster_id=cluster_id, cpu=%s, memory=%s, disk=%s"

        yield self.db.execute(sql, data)

    @run_on_executor
    def remote_deploy(self, params):
        ''' 远程部署主机
        '''
        ssh = SSH(hostname=params['public_ip'], username=params['username'], passwd=params['passwd'])
        ssh.exec(CMD_MONITOR)
        ssh.close()

    @coroutine
    def save_server_account(self, params):
        sql = " INSERT INTO server_account(public_ip, username, passwd) "\
              " VALUES(%s, %s, %s)"

        yield self.db.execute(sql, [params['public_ip'], params['username'], params['passwd']])

    @coroutine
    def migrate_server(self, params):
        sql = " UPDATE server SET cluster_id=%s WHERE id IN (%s) " % (params['cluster_id'], get_in_format(params['id']))

        yield self.db.execute(sql, params['id'])

    @coroutine
    def delete_server(self, params):
        sql = " DELETE FROM server WHERE id IN (%s) " % get_in_format(params['id'])

        yield self.db.execute(sql, params['id'])

    @coroutine
    def update_server(self, params):
        sql = " UPDATE server SET name=%s WHERE id=%s "

        yield self.db.execute(sql, [params['name'], params['id']])

    @coroutine
    def get_brief_list(self, cluster_id):
        ''' 集群详情中获取主机列表
        '''
        sql = " SELECT s.id, s.name, s.public_ip, i.status AS machine_status, i.region_id AS address " \
              " FROM server s " \
              " JOIN instance i USING(public_ip) " \
              " WHERE s.cluster_id=%s "
        cur = yield self.db.execute(sql, cluster_id)
        data = cur.fetchall()

        return data

    @coroutine
    def get_detail(self, id):
        ''' 获取主机详情
        '''
        sql = " SELECT s.id, s.cluster_id, c.name AS cluster_name, s.name, i.region_id, s.public_ip, i.status AS machine_status, " \
              "        s.business_status, i.cpu, i.memory, i.os_name, i.os_type, i.provider, i.create_time, i.expired_time, i.charge_type " \
              " FROM server s " \
              " JOIN instance i ON s.public_ip=i.public_ip " \
              " JOIN cluster c ON  s.cluster_id=c.id " \
              " WHERE s.id=%s "
        cur = yield self.db.execute(sql, id)
        data = cur.fetchone()

        return data

    @coroutine
    def get_performance(self, id):
        fields = 'cpu, memory, disk'

        raw_data = yield self.select(fields=fields, conds=['id=%s'], params=[id], one=True, ct=False, ut=False)

        data = {key:json.loads(raw_data[key]) for key in raw_data}

        return data

    @coroutine
    def fetch_instance_id(self, server_id):
        sql = " SELECT i.instance_id as instance_id FROM instance i JOIN server s USING(public_ip) WHERE s.id=%s "
        cur = yield self.db.execute(sql, server_id)
        data = cur.fetchone()

        return data['instance_id']

    @coroutine
    def stop_server(self, id):
        yield self.operate_server(id, 'StopInstance')

    @coroutine
    def start_server(self, id):
        yield self.operate_server(id, 'StartInstance')

    @coroutine
    def reboot_server(self, id):
        yield self.operate_server(id, 'RebootInstance')

    @coroutine
    def operate_server(self, id, cmd):
        instance_id = yield self.fetch_instance_id(id)

        params = {'Action': cmd, 'InstanceId': instance_id}
        payload = Aliyun.add_sign(params)

        yield self.get(payload)
        yield self.update_instance_status(INSTANCE_STATUS[cmd], instance_id)

    @coroutine
    def update_instance_status(self, status, instance_id):
        sql = " UPDATE instance SET status=%s WHERE instance_id=%s "

        yield self.db.execute(sql, [status, instance_id])