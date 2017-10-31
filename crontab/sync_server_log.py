import json
import time
import statistics
import sys
import datetime
import pymysql.cursors
from setting import settings

db = pymysql.connect(host=settings['mysql_host'],
                     user=settings['mysql_user'],
                     password=settings['mysql_password'],
                     db=settings['mysql_database'],
                     charset=settings['mysql_charset'],
                     cursorclass=pymysql.cursors.DictCursor)


class ServerLog:

    table_hour = 'server_log_hour'
    table_day = 'server_log_day'
    table_container_hour = 'container_log_hour'
    table_container_day = 'container_log_day'

    def __init__(self):
        self.data = []
        self.db = db
        self.ips = self.get_public_ip()
        self.end_time = 0
        self.start_time = 0

    def time_hour(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:00:00")
        now_tuple = datetime.datetime.strptime(now, "%Y-%m-%d %H:%M:%S").timetuple()
        self.end_time = int(time.mktime(now_tuple))
        self.start_time = self.end_time - 3600
        return

    def time_day(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        now_tuple = datetime.datetime.strptime(now, "%Y-%m-%d").timetuple()
        self.end_time = int(time.mktime(now_tuple))
        self.start_time = self.end_time - 86400
        return

    def get_public_ip(self):
        with self.db.cursor() as cur:
            sql = """
                SELECT public_ip FROM server
                """
            cur.execute(sql)
            ips = cur.fetchall()
        return [x['public_ip'] for x in ips]

    def get_data(self, ip, table, fields):
        with self.db.cursor() as cur:
            arg = [
                ip,
                self.start_time,
                self.end_time,
            ]
            sql = """
                SELECT {fields}
                FROM {table}
                WHERE public_ip = %s AND created_time >= %s AND created_time < %s
                """.format(table=table, fields=fields)
            cur.execute(sql, arg)
            data = cur.fetchall()
        return data

    def cal_container_performance(self, ip):
        resp = self.get_data(ip=ip, table='docker_stat', fields='container_name, content')
        if not resp:
            return {}
        containers, data = dict(), dict()
        for i in resp:
            name = i['container_name']
            if name not in containers:
                containers[name] = {
                                    'cpu': [],
                                    'block_input': [],
                                    'block_output': [],
                                    'memory_usage': [],
                                    'memory_limit': [],
                                    'memory_percent': [],
                                    'net_input': [],
                                    'net_output': []
                                    }
            content = json.loads(i['content'])
            containers[name]['cpu'].append(float(content['cpu']))
            containers[name]['block_input'].append(float(content['block_input']))
            containers[name]['block_output'].append(float(content['block_output']))
            containers[name]['memory_limit'].append(float(content['mem_limit']))
            containers[name]['memory_usage'].append(float(content['mem_usage']))
            containers[name]['memory_percent'].append(float(content['mem_percent']))
            containers[name]['net_input'].append(float(content['net_input']))
            containers[name]['net_output'].append(float(content['net_output']))

        for name in containers:
            if name not in data:
                data[name] = {
                    'cpu': {},
                    'block': {},
                    'memory': {},
                    'net': {}
                }
            data[name]['cpu'] = {'percent': "%.2f" % (statistics.mean(containers[name]['cpu']))}
            data[name]['block'] = {
                'block_input': "%.2f" % (statistics.mean(containers[name]['block_input'])),
                'block_output': "%.2f" % (statistics.mean(containers[name]['block_output'])),
            }
            data[name]['memory'] = {
                'memory_limit': "%.2f" % (statistics.mean(containers[name]['memory_limit'])),
                'memory_usage': "%.2f" % (statistics.mean(containers[name]['memory_usage'])),
                'memory_percent': "%.2f" % (statistics.mean(containers[name]['memory_percent']))
            }
            data[name]['net'] = {
                'net_input': "%.2f" % (statistics.mean(containers[name]['net_input'])),
                'net_output': "%.2f" % (statistics.mean(containers[name]['net_output']))
            }

        return data

    def cal_cpu(self, ip):
        data, avg = [], ''
        resp = self.get_data(ip=ip, table='cpu', fields='content')
        if resp:
            for x in resp:
                content = json.loads(x['content'])
                data.append(content['percent'])
            avg = "%.2f" % (statistics.mean(data))
        return {'percent': avg}

    def cal_disk(self, ip):
        total, free, percent = [], [], []
        total_avg, free_avg, percent_avg = '', '', ''
        resp = self.get_data(ip=ip, table='disk', fields='content')
        if resp:
            for x in resp:
                content = json.loads(x['content'])
                total.append(content['total'])
                free.append(content['free'])
                percent.append(content['percent'])
            total_avg = "%.2f" % (statistics.mean(total))
            free_avg = "%.2f" % (statistics.mean(free))
            percent_avg = "%.2f" % (statistics.mean(percent))
        return {'total': total_avg, 'free': free_avg, 'percent': percent_avg}

    def cal_memory(self, ip):
        total, free, percent, avaible = [], [], [], []
        total_avg, free_avg, percent_avg, avaible_avg = '', '', '', ''
        resp = self.get_data(ip=ip, table='memory', fields='content')
        if resp:
            for x in resp:
                content = json.loads(x['content'])
                total.append(content['total'])
                free.append(content['free'])
                percent.append(content['percent'])
                avaible.append(content['available'])
            total_avg = "%.2f" % (statistics.mean(total))
            free_avg = "%.2f" % (statistics.mean(free))
            percent_avg = "%.2f" % (statistics.mean(percent))
            avaible_avg = "%.2f" % (statistics.mean(avaible))
        return {
            'total': total_avg,
            'free': free_avg,
            'percent': percent_avg,
            'available': avaible_avg
        }

    def cal_net(self, ip):
        recv, send = [], []
        recv_avg, send_avg = '', ''
        resp = self.get_data(ip=ip, table='net', fields='content')
        if resp:
            for x in resp:
                content = json.loads(x['content'])
                recv.append(content['input'])
                send.append(content['output'])
            recv_avg = "%.2f" % (statistics.mean(recv))
            send_avg = "%.2f" % (statistics.mean(send))
        return {'input': recv_avg, 'output': send_avg}

    def cal(self):
        for ip in self.ips:
            one_ip = {
                'ip': ip,
                'cpu': json.dumps(self.cal_cpu(ip=ip)),
                'disk': json.dumps(self.cal_disk(ip=ip)),
                'memory': json.dumps(self.cal_memory(ip=ip)),
                'net': json.dumps(self.cal_net(ip=ip)),
                'containers': self.cal_container_performance(ip=ip)
            }
            self.data.append(one_ip)
        return

    def _save(self, params, table):
        with self.db.cursor() as cursor:
            arg = [
                params['ip'],
                self.start_time,
                self.end_time,
                params['cpu'],
                params['disk'],
                params['memory'],
                params['net']
            ]
            sql = """
                    INSERT INTO {table} set
                        public_ip=%s,
                        start_time=%s,
                        end_time=%s,
                        cpu_log=%s,
                        disk_log=%s,
                        memory_log=%s,
                        net_log=%s
                """.format(table=table)
            cursor.execute(sql, arg)

    def _save_container(self, params, table):
        for container in params['containers']:
            with self.db.cursor() as cursor:
                arg = [
                    params['ip'],
                    container,
                    self.start_time,
                    self.end_time,
                    json.dumps(params['containers'][container])
                ]
                sql = """
                        INSERT INTO {table} set
                            public_ip=%s,
                            container_name=%s,
                            start_time=%s,
                            end_time=%s,
                            content=%s
                    """.format(table=table)
                cursor.execute(sql, arg)

    def save_hour(self):
        for ip in self.data:
            self._save(params=ip, table=self.table_hour)
            self._save_container(params=ip,table=self.table_container_hour)
        self.db.commit()
        self.db.close()

    def save_day(self):
        for ip in self.data:
            self._save(params=ip, table=self.table_day)
            self._save_container(params=ip,table=self.table_container_day)
        self.db.commit()
        self.db.close()


def avg_hour():
    server = ServerLog()
    server.time_hour()
    server.cal()
    print("#### start sync server performance log ####")
    print("#### start sync hour ####")
    server.save_hour()
    print("#### end sync hour ####")
    print("#### end sync server performance log ####")


def avg_day():
    server = ServerLog()
    server.time_day()
    server.cal()
    print("#### start sync day ####")
    server.save_day()
    print("#### end sync day ####")
    print("#### end sync server performance log ####")


if __name__ == '__main__':
    if sys.argv[1] == 'hour':
        avg_hour()
    elif sys.argv[1] == 'day':
        avg_day()
