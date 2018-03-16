__author__ = 'Jon'

import json
from tornado.gen import coroutine, sleep

from service.base import BaseService
from utils.general import get_formats
from utils.aliyun import Aliyun
from utils.qcloud import Qcloud
from utils.zcloud import Zcloud
from constant import UNINSTALL_CMD, DEPLOYED, LIST_CONTAINERS_CMD, START_CONTAINER_CMD, STOP_CONTAINER_CMD, \
                     DEL_CONTAINER_CMD, CONTAINER_INFO_CMD, ALIYUN_NAME, QCLOUD_NAME, FULL_DATE_FORMAT, ZCLOUD_NAME, \
                     SERVERS_REPORT_INFO, TCLOUD_STATUS
from utils.security import Aes
from utils.general import get_in_formats, json_loads, json_dumps

class ServerService(BaseService):
    table = 'server'
    fields = 'id, name, public_ip, business_status, cluster_id, instance_id, lord, form'

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

        if params.get('docker'):
            for (k, v) in params['docker'].items():
                self._save_docker_report(base_data + [k] + [json.dumps(v)])

        # 保存最新至redis
        public_ip = params.pop('public_ip')
        self.redis.hset(SERVERS_REPORT_INFO, public_ip, json_dumps(params))

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
    def fetch_instance_id(self, public_ip):
        cur = yield self.db.execute(" SELECT instance_id FROM instance WHERE public_ip = %s ", [public_ip])
        data = cur.fetchone()

        return data.get('instance_id', '') if data else ''

    @coroutine
    def add_server(self, params):
        instance_id = yield self.fetch_instance_id(params['public_ip'])

        sql = " INSERT INTO server(name, public_ip, cluster_id, instance_id, lord, form) " \
              " VALUES(%s, %s, %s, %s, %s, %s)"

        yield self.db.execute(sql, [params['name'], params['public_ip'], params['cluster_id'], instance_id, params['lord'], params['form']])

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

        params['cmd'] = UNINSTALL_CMD
        yield self.remote_ssh(params)

        for table in ['server', 'server_account']:
            yield self._delete_server_info(table, params['public_ip'])

        self.redis.hdel(DEPLOYED, params['public_ip'])

    @coroutine
    def delete_server(self, params):
        for server_id in params['id']:
            yield self._delete_server(server_id=server_id)

    @coroutine
    def update_server(self, params):
        sql = " UPDATE server SET name=%s WHERE id=%s "

        yield self.db.execute(sql, [params['name'], params['id']])

    @coroutine
    def get_brief_list(self, **cond):
        ''' 集群详情中获取主机列表
        '''
        arg = []
        extra = ''

        if len(cond) > 1: # 暂时保留cluster_id，但实际没用到
            extra = 'WHERE '
            e = []

            if cond.get('provider'):
                e.append(get_in_formats(field='i.provider', contents=cond['provider']))
                if isinstance(cond['provider'], list):
                    arg.extend(cond['provider'])
                else:
                    arg.append(cond['provider'])

            if cond.get('region'):
                e.append(get_in_formats(field='i.region_name', contents=cond['region']))
                if isinstance(cond['region'], list):
                    arg.extend(cond['region'])
                else:
                    arg.append(cond['region'])

            if cond.get('lord'):
                e.append('s.lord=%s')
                arg.append(cond['lord'])

            if cond.get('form'):
                e.append('s.form=%s')
                arg.append(cond['form'])

            extra += ' AND '.join(e)

        sql = """
            SELECT s.id, s.name, s.public_ip, i.provider, i.instance_name, i.region_name AS address, i.status AS machine_status
            FROM server s
            JOIN instance i USING(instance_id)
            """+"""
            {where}
            ORDER BY i.provider
        """.format(where=extra)

        cur = yield self.db.execute(sql, arg)
        data = cur.fetchall()

        # 添加最新上报信息
        report_info = self.redis.hgetall(SERVERS_REPORT_INFO)
        for d in data:
            info = json_loads(report_info.get(d['public_ip']))
            d.update(info)

        data = sorted(data, key=lambda x: x['name'], reverse=True)
        return data

    @coroutine
    def get_detail(self, id):
        ''' 获取主机详情
        '''
        sql = """ 
                SELECT s.id, s.cluster_id, DATE_FORMAT(s.create_time, %s) AS server_created_time , c.name AS cluster_name, 
                       s.name, s.public_ip, i.status AS machine_status, i.region_id, i.region_name,
                       s.business_status, i.cpu, i.memory, i.os_name, i.os_type, i.provider, i.create_time, i.expired_time, 
                       i.charge_type, i.instance_id, i.security_group_ids, i.instance_network_type, i.InternetMaxBandwidthIn,
                       i.InternetMaxBandwidthOut, i.SystemDisk_ID, i.SystemDisk_Type, i.SystemDisk_Size
                FROM server s 
                JOIN instance i ON s.instance_id=i.instance_id 
                JOIN cluster c ON  s.cluster_id=c.id 
                WHERE s.id=%s 
              """
        cur = yield self.db.execute(sql, [FULL_DATE_FORMAT, id])
        data = cur.fetchone()

        return data

    @coroutine
    def _get_performance(self, table, params):
        """
        :param table: cpu/memory/disk
        :param params: {'public_ip': str, 'start_time': timestamp, 'end_time': timestamp}
        """
        id_sql = """
                SELECT id FROM {table} 
                WHERE public_ip=%s AND created_time>=%s AND created_time<%s
                ORDER BY created_time DESC
                """.format(table=table)
        cur = yield self.db.execute(id_sql, [params['public_ip'], params['start_time'], params['end_time']])
        ids = [i['id'] for i in cur.fetchall()]
        if not ids:
            return []
        step = len(ids)//7
        choose_id = ids

        if step:
            choose_id = [ids[i] for i in range(0, len(ids), step)]

        ids = get_in_formats(field='id', contents=choose_id)
        sql = """
              SELECT created_time,content FROM {table}
              WHERE {ids}
              """.format(table=table, ids=ids)
        cur = yield self.db.execute(sql, choose_id)

        data = []
        for x in cur.fetchall():
            created_time = {'created_time': x['created_time']}
            content = json.loads(x['content'])
            content.update(created_time)
            data.append(content)
        return data

    @coroutine
    def _get_performance_page(self, params):
        data = []
        start_page = (params['now_page'] - 1) * params['page_number']
        arg = [
            params['public_ip'],
            params['start_time'],
            params['end_time'],
            start_page,
            params['page_number']
        ]
        sql = """
            SELECT c.created_time AS created_time, c.content AS  cpu, d.content AS disk, m.content AS memory, n.content AS net
            FROM cpu AS c
            JOIN disk AS  d ON c.public_ip=d.public_ip AND c.created_time=d.created_time
            JOIN memory AS m ON c.public_ip=m.public_ip AND c.created_time=m.created_time
            JOIN net AS  n ON c.public_ip=n.public_ip AND c.created_time=n.created_time
            WHERE c.public_ip=%s  AND c.created_time>=%s AND c.created_time<%s
            LIMIT %s, %s
        """
        cur = yield self.db.execute(sql, arg)
        for i in cur.fetchall():
            one_record = {
                'created_time': i['created_time'],
                'cpu': json.loads(i['cpu']),
                'disk': json.loads(i['disk']),
                'memory':json.loads(i['memory']),
                'net': json.loads(i['net']),
            }
            data.append(one_record)
        return data

    @coroutine
    def _get_performance_avg(self, table, params):
        data = []
        start_page = (params['now_page'] - 1) * params['page_number']
        arg = [
            params['public_ip'],
            params['start_time'],
            params['end_time'],
            start_page,
            params['page_number']
        ]
        sql = """
                SELECT end_time,cpu_log, disk_log, memory_log, net_log
                FROM {table}
                WHERE public_ip=%s AND start_time>=%s AND end_time<=%s 
                LIMIT %s, %s
            """.format(table=table)
        cur = yield self.db.execute(sql, arg)
        for i in cur.fetchall():
            one_record = {
                'created_time': i['end_time'],
                'cpu': json.loads(i['cpu_log']),
                'disk': json.loads(i['disk_log']),
                'memory': json.loads(i['memory_log']),
                'net': json.loads(i['net_log']),
            }
            data.append(one_record)
        return data

    @coroutine
    def get_performance(self, params):
        params['public_ip'] = yield self.fetch_public_ip(params['id'])

        data = {}
        if params['type'] == 0:
            data['cpu'] = yield self._get_performance('cpu', params)
            data['memory'] = yield self._get_performance('memory', params)
            data['disk'] = yield self._get_performance('disk', params)
            data['net'] = yield self._get_performance('net', params)
        elif params['type'] == 1:
            data = yield self._get_performance_page(params)
        elif params['type'] == 2:
            data = yield self._get_performance_avg('server_log_hour', params)
        elif params['type'] == 3:
            data = yield self._get_performance_avg('server_log_day', params)
        return data

    @coroutine
    def fetch_public_ip(self, server_id):
        sql = " SELECT public_ip as public_ip FROM server WHERE id=%s "
        cur = yield self.db.execute(sql, server_id)
        data = cur.fetchone()
        return data['public_ip']

    @coroutine
    def fetch_server_id(self, public_ip):
        sql = " SELECT id as server_id FROM server WHERE public_ip=%s "
        cur = yield self.db.execute(sql, public_ip)
        data = cur.fetchone()
        return data['server_id']

    @coroutine
    def fetch_instance_info(self, server_id):
        sql = " SELECT i.* FROM instance i JOIN server s USING(instance_id) WHERE s.id=%s "
        cur = yield self.db.execute(sql, server_id)
        info = cur.fetchone()
        return info

    @coroutine
    def _change_ip(self, cloud, info):
        new_ip = cloud.get_public_ip(info)
        old_ip = info['public_ip']

        while not new_ip or new_ip == old_ip:
            yield sleep(1)
            new_ip = cloud.get_public_ip(info)

        self.redis.hset(DEPLOYED, new_ip, 1)
        self.redis.hdel(DEPLOYED, old_ip)
        yield self.update(sets={'public_ip': new_ip}, conds={'public_ip': old_ip})
        yield self.db.execute('UPDATE instance SET public_ip = %s WHERE public_ip = %s', [new_ip, old_ip])
        yield self.db.execute('UPDATE server_account SET public_ip = %s WHERE public_ip = %s', [new_ip, old_ip])

    def _produce_cloud(self, provider):
        clouds = {
            ALIYUN_NAME: Aliyun,
            QCLOUD_NAME: Qcloud,
            ZCLOUD_NAME: Zcloud
        }

        return clouds[provider]

    @coroutine
    def stop_server(self, id):
        yield self._operate_server(id, 'stop')
        yield self.change_instance_status(status=TCLOUD_STATUS[9], id=id)

    @coroutine
    def start_server(self, id):
        yield self._operate_server(id, 'start')
        yield self.change_instance_status(status=TCLOUD_STATUS[8], id=id)

    @coroutine
    def reboot_server(self, id):
        yield self._operate_server(id, 'reboot')
        yield self.change_instance_status(status=TCLOUD_STATUS[7], id=id)

    @coroutine
    def _operate_server(self, id, cmd):
        info = yield self.fetch_instance_info(id)

        cloud = self._produce_cloud(info['provider'])

        # 亚马逊云与微软云，会变化public_ip
        if info['provider'] == ZCLOUD_NAME:
            getattr(cloud, cmd)(info)

            if cmd in ['start', 'reboot']:
                yield self._change_ip(cloud, info)

            return

        params = getattr(cloud, cmd)(info)
        payload = cloud.add_sign(params)

        yield self.get(payload, host=cloud.domain)

    @coroutine
    def get_instance_status(self, instance_id):
        ''' 根据instance_id,查询当前主机开关状态
        '''
        sql = " SELECT status FROM instance WHERE instance_id=%s "
        cur = yield self.db.execute(sql, instance_id)
        data = cur.fetchone()

        return data.get('status')

    @coroutine
    def get_containers(self, params):
        return []
        info = yield self.fetch_ssh_login_info(params)
        params.update(info)
        params['cmd'] = LIST_CONTAINERS_CMD

        out, err = yield self.remote_ssh(params)

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
        login_info = yield self.fetch_ssh_login_info({'server_id': params['id']})
        login_info.update({'cmd': cmd})

        _, err = yield self.remote_ssh(login_info)

        if err:
            raise ValueError

    @coroutine
    def get_docker_performance(self, params):
        # 通过主机id(server_id)获取公共IP
        params['public_ip'] = yield self.fetch_public_ip(params['id'])
        if not params['public_ip']:
            raise ValueError('主机不存在')

        data = {}
        if params['type'] == 0:
            data = yield self._get_container_performance(params)
        elif params['type'] == 1:
            data = yield self._get_container_performance_page(params)
        elif params['type'] == 2:
            data = yield self._get_container_performance_avg('container_log_hour', params)
        elif params['type'] == 3:
            data = yield self._get_container_performance_avg('container_log_day', params)
        return data

    @coroutine
    def _get_container_performance(self, params):

        sql = """
                  SELECT id from {table}
                  WHERE public_ip=%s AND container_name=%s
                  AND created_time>= %s AND created_time < %s
                  ORDER BY created_time DESC
              """.format(table='docker_stat')
        cur = yield self.db.execute(sql, [params['public_ip'], params['container_name'],
                                    params['start_time'], params['end_time']])
        ids = [i['id'] for i in cur.fetchall()]
        if not ids:
            return {}
        step = len(ids)//7
        choose_id = ids
        if step:
            choose_id = [ids[i] for i in range(0, len(ids), step)]
        ids = get_in_formats(field='id', contents=choose_id)
        sql = """
                SELECT created_time, content FROM {table}
                WHERE {ids}
                """.format(table='docker_stat', ids=ids)
        cur = yield self.db.execute(sql, choose_id)
        data = {
            'cpu': [],
            'memory': [],
            'net': [],
            'block': []
        }
        for x in cur.fetchall():
            content = json.loads(x['content'])
            cpu = {
                    'percent': content['cpu'],
                    'created_time': x['created_time'],
                }
            data['cpu'].append(cpu)

            memory = {
                    'percent': content['mem_percent'],
                    'created_time': x['created_time'],
                }
            data['memory'].append(memory)

            net = {
                    'input': content['net_input'],
                    'output': content['net_output'],
                    'created_time': x['created_time'],
            }
            data['net'].append(net)

            block = {
                    'input': content['block_input'],
                    'output': content['block_output'],
                    'created_time': x['created_time'],
            }
            data['block'].append(block)

        return data

    @coroutine
    def _get_container_performance_page(self, params):
        data = []
        start_page = (params['now_page'] - 1) * params['page_number']
        arg = [
            params['public_ip'],
            params['start_time'],
            params['end_time'],
            start_page,
            params['page_number']
        ]
        sql = """
                SELECT created_time, content FROM {table}
                WHERE public_ip=%s  AND created_time>=%s AND created_time<%s
                LIMIT %s, %s
            """.format(table='docker_stat')
        cur = yield self.db.execute(sql, arg)
        for i in cur.fetchall():
            content = json.loads(i['content'])
            one_record = {
                'created_time': i['created_time'],
                'cpu': {'percent': content['cpu']},
                'block': {
                        'block_input': content['block_input'],
                        'block_output': content['block_output'],
                },
                'memory': {
                        'mem_limit': content['mem_limit'],
                        'mem_usage': content['mem_usage'],
                        'mem_percent': content['mem_percent']
                        },
                'net': {
                        'net_input': content['net_input'],
                        'net_output': content['net_output'],
                        },
            }
            data.append(one_record)
        return data

    @coroutine
    def _get_container_performance_avg(self, table, params):
        data = []
        start_page = (params['now_page'] - 1) * params['page_number']
        arg = [
            params['public_ip'],
            params['container_name'],
            params['start_time'],
            params['end_time'],
            start_page,
            params['page_number']
        ]
        sql = """
                SELECT end_time, content
                FROM {table}
                WHERE public_ip=%s AND container_name=%s AND start_time>=%s AND end_time<=%s 
                LIMIT %s, %s
            """.format(table=table)
        cur = yield self.db.execute(sql, arg)
        for i in cur.fetchall():
            content = json.loads(i['content'])
            one_record = {
                'created_time': i['end_time'],
                'cpu': content['cpu'],
                'block': content['block'],
                'memory': content['memory'],
                'net': content['net'],
            }
            data.append(one_record)
        return data

    @coroutine
    def get_container_info(self, params):
        params['cmd'] = CONTAINER_INFO_CMD % (params['container_id'])

        raw_out, err = yield self.remote_ssh(params)
        json_out = json.loads(raw_out[0])
        data = {
            'name': json_out['Name'],
            'status': json_out['State'].get('Status', 'dead'),
            'created': json_out['Created'],
            'runtime': {
                'hostname': params['server_name'],
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

    @coroutine
    def change_instance_status(self, status, id):
        ip = yield self.fetch_public_ip(server_id=id)
        sql = """
        update instance set status=%s where public_ip=%s
        """
        yield self.db.execute(sql, [status, ip])
