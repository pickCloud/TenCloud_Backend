__author__ = 'Jon'

import json
from tornado.gen import coroutine, Task, sleep

from service.base import BaseService
from utils.general import get_formats
from utils.aliyun import Aliyun
from utils.qcloud import Qcloud
from utils.zcloud import Zcloud
from constant import UNINSTALL_CMD, DEPLOYED, LIST_CONTAINERS_CMD, START_CONTAINER_CMD, STOP_CONTAINER_CMD, \
                     DEL_CONTAINER_CMD, CONTAINER_INFO_CMD, ALIYUN_NAME, QCLOUD_NAME, FULL_DATE_FORMAT, ZCLOUD_NAME
from utils.security import Aes
from utils.general import get_in_formats

class ServerService(BaseService):
    table = 'server'
    fields = 'id, name, public_ip, business_status, cluster_id, instance_id, cid'

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
    def fetch_instance_id(self, public_ip):
        cur = yield self.db.execute(" SELECT instance_id FROM instance WHERE public_ip = %s ", [public_ip])
        data = cur.fetchone()

        return data.get('instance_id', '') if data else ''

    @coroutine
    def add_server(self, params):
        instance_id = yield self.fetch_instance_id(params['public_ip'])

        sql = " INSERT INTO server(name, public_ip, cluster_id, instance_id) " \
              " VALUES(%s, %s, %s, %s)"

        yield self.db.execute(sql, [params['name'], params['public_ip'], params['cluster_id'], instance_id])

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
    def get_brief_list(self, cluster_id, provider='', region=''):
        extra = ''
        arg = [cluster_id]
        if provider and region:
            extra = 'WHERE i.provider=%s AND i.region_name=%s'
            arg.extend([provider, region])
        elif provider and (not region):
            extra = 'WHERE i.provider=%s'
            arg.extend([provider])
        elif (not provider) and region:
            extra = 'WHERE i.region_name=%s'
            arg.extend([region])

        ''' 集群详情中获取主机列表
        '''
        sql = """
            SELECT sss.id, sss.name, sss.public_ip, COALESCE(sss.cpu_content, '{}') AS cpu_content,
                   COALESCE(sss.net_content, '{}') AS net_content, COALESCE(sss.memory_content, '{}') AS memory_content, 
                   COALESCE(sss.disk_content, '{}') AS disk_content, sss.report_time,
                   i.provider, i.instance_name, i.region_name AS address, i.status AS machine_status
            FROM(
                SELECT ss.*, c.content AS cpu_content, n.content AS net_content, m.content AS memory_content
                FROM
                (
                    SELECT s.*, ddd.content AS disk_content, ddd.created_time AS report_time
                    FROM server s
                    JOIN(
                        SELECT dd.public_ip, dd.content, dd.created_time
                        FROM disk dd
                        JOIN(
                            SELECT public_ip, max(created_time) AS created_time
                            FROM disk
                            GROUP BY public_ip
                        ) AS d ON dd.public_ip = d.public_ip AND dd.created_time = d.created_time
                    ) AS ddd using(public_ip)
                    WHERE s.cluster_id = %s
                ) AS ss
                LEFT JOIN cpu AS c ON ss.public_ip = c.public_ip AND ss.report_time = c.created_time
                LEFT JOIN net AS n ON ss.public_ip = n.public_ip AND ss.report_time = n.created_time
                LEFT JOIN memory AS m ON ss.public_ip = m.public_ip AND ss.report_time = m.created_time
            ) sss
            LEFT JOIN instance AS i ON sss.public_ip = i.public_ip
            """+"""
            {where}
            ORDER BY i.provider
            """.format(where=extra)
        cur = yield self.db.execute(sql, arg)
        data = cur.fetchall()
        return data

    @coroutine
    def get_detail(self, id):
        ''' 获取主机详情
        '''
        sql = """ 
                SELECT s.id, s.cluster_id, DATE_FORMAT(s.create_time, %s) AS server_created_time , c.name AS cluster_name, 
                       s.name, s.public_ip, i.status AS machine_status, i.region_id, i.region_name,
                       s.business_status, i.cpu, i.memory, i.os_name, i.os_type, i.provider, i.create_time, i.expired_time, 
                       i.charge_type, i.instance_id
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

        data = [[x['created_time'], json.loads(x['content'])] for x in cur.fetchall()]
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
            JOIN disk AS  d ON c.public_ip=d.public_ip
            JOIN memory AS m ON c.public_ip=m.public_ip
            JOIN net AS  n ON c.public_ip=n.public_ip
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

        yield Task(self.redis.hset, DEPLOYED, new_ip, 1)
        yield Task(self.redis.hdel, DEPLOYED, old_ip)
        yield self.update(sets=['public_ip=%s'], conds=['public_ip=%s'], params=[new_ip, old_ip])
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

    @coroutine
    def start_server(self, id):
        yield self._operate_server(id, 'start')

    @coroutine
    def reboot_server(self, id):
        yield self._operate_server(id, 'reboot')

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

        info = yield self.fetch_ssh_login_info(params)
        params.update(info)

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
    def get_docker_performance(self, params):
        params['public_ip'] = yield self.fetch_public_ip(params['server_id'])

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
            data['cpu'].append([x['created_time'], {'percent':content['cpu']}])
            data['memory'].append([x['created_time'], {'percent':content['mem_percent']}])
            data['net'].append([x['created_time'], {'input': content['net_input'],
                                                'output': content['net_output']}])
            data['block'].append([x['created_time'], {'input': content['block_input'],
                                                'output': content['block_output']}])

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
        cmd = CONTAINER_INFO_CMD % (params['container_id'])

        raw_out, err = yield self.remote_ssh(params, cmd=cmd)
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
