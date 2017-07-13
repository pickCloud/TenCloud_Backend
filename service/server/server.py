__author__ = 'Jon'

import json
from tornado.gen import coroutine, Task

from service.base import BaseService
from utils.general import get_formats
from utils.aliyun import Aliyun
from constant import UNINSTALL_CMD, DEPLOYED, LIST_CONTAINERS_CMD, START_CONTAINER_CMD, STOP_CONTAINER_CMD, DEL_CONTAINER_CMD, CONTAINER_INFO_CMD
from utils.security import Aes


class ServerService(BaseService):
    table = 'server'
    fields = 'id, name, address, ip, machine_status, business_status'

    @coroutine
    def save_report(self, params):
        """ 保存主机上报的信息
        """
        base_data = [params['public_ip'], params['time']]
        base_sql = 'INSERT INTO %s(public_ip, created_time,content)'
        suffix = ' values(%s,%s,%s)'
        for table in ['cpu', 'memory', 'disk', 'net']:
            content = json.dumps(params[table])
            sql = (base_sql % table) + suffix
            yield self.db.execute(sql, base_data + [content])

        for (k, v) in params['docker'].items():
            self._save_docker_report(base_data + [k] + [json.dumps(v)])

    @coroutine
    def _save_docker_report(self, params):
        sql = "INSERT INTO docker_stat(public_ip, created_time, container_name,  content)" \
            "VALUES(%s, %s, %s, %s)"
        yield self.db.execute(sql, params)

    @coroutine
    def save_server_account(self, params):
        sql = " INSERT INTO server_account(public_ip, username, passwd) " \
              " VALUES(%s, %s, %s)"

        yield self.db.execute(sql, [params['public_ip'], params['username'], params['passwd']])

    @coroutine
    def add_server(self, params):
        sql = " INSERT INTO server(name, public_ip, cluster_id) " \
              " VALUES(%s, %s, %s)"

        yield self.db.execute(sql, [params['name'], params['public_ip'], params['cluster_id']])

    @coroutine
    def migrate_server(self, params):
        sql = " UPDATE server SET cluster_id=%s WHERE id IN (%s) " % (params['cluster_id'], get_formats(params['id']))

        yield self.db.execute(sql, params['id'])

    @coroutine
    def fetch_ssh_login_info(self, params):
        ''' 获取ssh登录信息, IP/用户名/密码
        :param params: dict e.g. {'server_id': str, 'public_ip': str}
        :return:
        '''

        sql = "SELECT s.public_ip, sa.username, sa.passwd FROM server s JOIN server_account sa USING(public_ip) WHERE "
        conds, data = [], []
        if params.get('server_id'):
            conds.append('s.id=%s')
            data.append(params['server_id'])

        if params.get('public_ip'):
            conds.append('s.public_ip=%s')
            data.append(params['public_ip'])

        sql += ' AND '.join(conds)

        cur = yield self.db.execute(sql, data)
        data = cur.fetchone()

        data['passwd'] = Aes.decrypt(data['passwd'])

        return data

    @coroutine
    def _delete_server_info(self, table, public_ip):
        base_sql = "DELETE FROM %s " % table
        sql = base_sql + "WHERE public_ip=%s"
        yield self.db.execute(sql, public_ip)

    @coroutine
    def _delete_server(self, server_id):
        params = yield self.fetch_ssh_login_info({'server_id': server_id})

        yield self.remote_ssh(params, cmd=UNINSTALL_CMD)

        for table in ['server', 'server_account']:
            yield self._delete_server_info(table, params['public_ip'])

        yield Task(self.redis.hdel, DEPLOYED, params['public_ip'])

    @coroutine
    def delete_server(self, params):
        for server_id in params['id']:
            yield self._delete_server(server_id=server_id)

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
        sql = " SELECT s.id, s.cluster_id, c.name AS cluster_name, s.name, i.region_id, s.public_ip, i.status AS machine_status, i.region_id, " \
              "        s.business_status, i.cpu, i.memory, i.os_name, i.os_type, i.provider, i.create_time, i.expired_time, i.charge_type, i.instance_id" \
              " FROM server s " \
              " JOIN instance i ON s.public_ip=i.public_ip " \
              " JOIN cluster c ON  s.cluster_id=c.id " \
              " WHERE s.id=%s "
        cur = yield self.db.execute(sql, id)
        data = cur.fetchone()

        return data

    @coroutine
    def _get_performance(self, table, params):
        '''
        :param table: cpu/memory/disk
        :param params: {'public_ip': str, 'start_time': timestamp, 'end_time': timestamp}
        '''
        sql = """
            SELECT created_time,content FROM {table}
            WHERE public_ip=%s AND created_time>=%s AND created_time<%s
        """.format(table=table)

        cur = yield self.db.execute(sql, [params['public_ip'], params['start_time'], params['end_time']])

        return [[x['created_time'], json.loads(x['content'])] for x in cur.fetchall()]

    @coroutine
    def get_performance(self, params):
        params['public_ip'] = yield self.fetch_public_ip(params['id'])

        data = {}

        data['cpu'] = yield self._get_performance('cpu', params)
        data['memory'] = yield self._get_performance('memory', params)
        data['disk'] = yield self._get_performance('disk', params)
        data['net'] = yield self._get_performance('net', params)

        return data

    @coroutine
    def fetch_public_ip(self, server_id):
        sql = " SELECT public_ip as public_ip FROM server WHERE id=%s "
        cur = yield self.db.execute(sql, server_id)
        data = cur.fetchone()
        return data['public_ip']

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

    @coroutine
    def get_instance_status(self, instance_id):
        ''' 根据instance_id,查询当前主机开关状态
        '''
        sql = " SELECT status FROM instance WHERE instance_id=%s "
        cur = yield self.db.execute(sql, instance_id)
        data = cur.fetchone()

        return data.get('status')

    @coroutine
    def get_containers(self, id):
        params = yield self.fetch_ssh_login_info({'server_id': id})

        out, err = yield self.remote_ssh(params, cmd=LIST_CONTAINERS_CMD)

        if err:
            raise ValueError

        data = [i.split(',') for i in out]

        return data

    @coroutine
    def start_container(self, params):
        yield self.operate_container(params, cmd=START_CONTAINER_CMD.format(container_id=params['container_id']))

    @coroutine
    def stop_container(self, params):
        yield self.operate_container(params, cmd=STOP_CONTAINER_CMD.format(container_id=params['container_id']))

    @coroutine
    def del_container(self, params):
        yield self.operate_container(params, cmd=DEL_CONTAINER_CMD.format(container_id=params['container_id']))

    @coroutine
    def operate_container(self, params, cmd):
        login_info = yield self.fetch_ssh_login_info({'server_id': params['server_id']})

        _, err = yield self.remote_ssh(login_info, cmd=cmd)

        if err:
            raise ValueError

    @coroutine
    def get_docker_performance(self,params):
        params['public_ip'] = yield self.fetch_public_ip(params['server_id'])

        sql = """
                  SELECT created_time, content from docker_stat
                  WHERE public_ip=%s AND container_name=%s 
                  AND created_time>= %s AND created_time < %s
              """
        cur = yield self.db.execute(sql, [params['public_ip'], params['container_name'],
                                    params['start_time'], params['end_time']])
        data = {
            'cpu': [],
            'memory': [],
            'net': [],
            'block': []
        }
        for x in cur.fetchall():
            content = json.loads(x['content'])
            data['cpu'].append([x['created_time'], {'percent':content['cpu']}])
            data['memory'].append([x['created_time'], {'percent':content['mem_percent']}])
            data['net'].append([x['created_time'], {'input': content['net_input'],
                                                'output': content['net_output']}])
            data['block'].append([x['created_time'], {'input': content['block_input'],
                                                'output': content['block_output']}])

        return data

    @coroutine
    def get_container_info(self, params):
        cmd = CONTAINER_INFO_CMD % (params['container_id'])

        raw_out, err = yield self.remote_ssh(params, cmd=cmd)
        json_out = json.loads(raw_out[0])
        data = {
            'name': json_out['Name'],
            'status': json_out['State'].get('Status', 'dead'),
            'created': json_out['Created'],
            'runtime': {
                'hostname': json_out['Config'].get('Hostname', ""),
                'ip': params['public_ip'],
                'port': [key.split('/')[0] for key in json_out['Config'].get('ExposedPorts', {}).keys()],
                'address': "http://{ip}".format(ip=params['public_ip'])
            },
            'container': {
                'workingdir': json_out['Config'].get('WorkingDir', ''),
                'cmd': ' '.join(x for x in json_out['Config'].get('Cmd') or ['']),  # 防止cmd为null
                'volumes': json_out['Config'].get('Volumes', ''),
                'volumesfrom': json_out['HostConfig'].get('VolumesFrom', ''),
            },
            'network': {
                'dns': json_out['HostConfig'].get('Dns', ''),
                'links': json_out['HostConfig'].get('Links', ''),
                'portbind': json_out['NetworkSettings'].get('Ports', '')
            }
        }
        return data, err

