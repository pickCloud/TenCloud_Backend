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

    def get_data(self, ip, table):
        with self.db.cursor() as cur:
            arg = [
                ip,
                self.start_time,
                self.end_time,
            ]
            sql = """
                SELECT content
                FROM {table}
                WHERE public_ip = %s AND created_time >= %s AND created_time < %s
                """.format(table=table)
            cur.execute(sql, arg)
            data = cur.fetchall()
        return data

    def cal_cpu(self, ip):
        data = []
        for x in self.get_data(ip=ip, table='cpu'):
            content = json.loads(x['content'])
            data.append(content['percent'])
        avg = statistics.mean(data)
        return {'percent': avg}

    def cal_disk(self, ip):
        total, free, percent = [], [], []
        for x in self.get_data(ip=ip, table='disk'):
            content = json.loads(x['content'])
            total.append(content['total'])
            free.append(content['free'])
            percent.append(content['percent'])
        total_avg = statistics.mean(total)
        free_avg = statistics.mean(free)
        percent_avg = statistics.mean(percent)
        return {'total': total_avg, 'free': free_avg, 'percent': percent_avg}

    def cal_memory(self, ip):
        total, free, percent, avaible = [], [], [], []
        for x in self.get_data(ip=ip, table='memory'):
            content = json.loads(x['content'])
            total.append(content['total'])
            free.append(content['free'])
            percent.append(content['percent'])
            avaible.append(content['available'])
        total_avg = statistics.mean(total)
        free_avg = statistics.mean(free)
        percent_avg = statistics.mean(percent)
        avaible_avg = statistics.mean(avaible)
        return {
            'total': total_avg,
            'free': free_avg,
            'percent': percent_avg,
            'available': avaible_avg
        }

    def cal_net(self, ip):
        recv, send = [], []
        for x in self.get_data(ip=ip, table='net'):
            content = json.loads(x['content'])
            recv.append(content['input'])
            send.append(content['output'])
        recv_avg = statistics.mean(recv)
        send_avg = statistics.mean(send)
        return {'input': recv_avg, 'output': send_avg}

    def cal(self):
        for ip in self.ips:
            one_ip = {
                'ip': ip,
                'cpu': json.dumps(self.cal_cpu(ip=ip)),
                'disk': json.dumps(self.cal_disk(ip=ip)),
                'memory': json.dumps(self.cal_memory(ip=ip)),
                'net': json.dumps(self.cal_net(ip=ip))
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
        self.db.commit()

    def save_hour(self):
        for ip in self.data:
            self._save(params=ip, table=self.table_hour)
        self.db.close()

    def save_day(self):
        for ip in self.data:
            self._save(params=ip, table=self.table_day)
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