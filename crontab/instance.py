__author__ = 'Jon'

'''获取各种云的实例,并更新数据库
'''
import sys
import argparse
import time
import traceback
import logging

logging.basicConfig(stream=sys.stdout, level=logging.WARN)

import pymysql.cursors
from utils.aliyun import Aliyun
from utils.qcloud import Qcloud
from utils.zcloud import Zcloud
from utils.datetool import seconds_to_human
from utils.general import get_formats, get_in_formats
from constant import ALIYUN_REGION_LIST, QCLOUD_REGION_LIST, QCLOUD_STATUS, QCLOUD_PAYMODE, ALIYUN_NAME, \
    QCLOUD_NAME, ALIYUN_REGION_NAME, QCLOUD_REGION_NAME, ALIYUN_STATUS, ZCLOUD_REGION_LIST, ZCLOUD_STATUS, \
    ZCLOUD_TYPE, ZCLOUD_NAME, ZCLOUD_REGION_NAME
from setting import settings
from requests_futures.sessions import FuturesSession
from concurrent.futures import ThreadPoolExecutor, wait
from DBUtils.PooledDB import PooledDB


pool = PooledDB(pymysql, maxcached=1, maxconnections=1,
                host=settings['mysql_host'],
                user=settings['mysql_user'],
                password=settings['mysql_password'],
                db=settings['mysql_database'],
                charset=settings['mysql_charset'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True)
DB = pool.connection()

MAX_WORKERS = 20


class Instance:
    def __init__(self):
        self.provider = ''
        self.data = {}
        self.db_data = {}
        self.db = DB
        self.cur = ''

    def get_aliyun(self):
        self.provider = ALIYUN_NAME

        with FuturesSession(max_workers=MAX_WORKERS) as session:
            futures = []

            for region in ALIYUN_REGION_LIST:
                url = Aliyun.make_url({'Action': 'DescribeInstances', 'RegionId': region})
                futures.append(session.get(url))

            for f in futures:
                r = f.result()
                info = r.json()

                for j in info['Instances']['Instance']:
                    self.data[j.get('InstanceId')] = {
                        'instance_id': j.get('InstanceId'),
                        'instance_name': j.get('InstanceName', ''),
                        'region_id': j.get('RegionId', ''),
                        'region_name': ALIYUN_REGION_NAME.get(j.get('RegionId', ''), j.get('RegionId', '')),
                        'hostname': j.get('HostName', ''),
                        'image_id': j.get('ImageId', ''),
                        'status': ALIYUN_STATUS.get(j.get('Status', ''), j.get('Status', '')),
                        'inner_ip': (j.get('InnerIpAddress', {}).get('IpAddress') or [''])[0],
                        'public_ip': (j.get('PublicIpAddress', {}).get('IpAddress') or [''])[0],
                        'cpu': j.get('Cpu', 0),
                        'memory': j.get('Memory', 0),
                        'os_name': j.get('OSName', ''),
                        'os_type': j.get('OSType', ''),
                        'create_time': j.get('CreationTime', ''),
                        'expired_time': j.get('ExpiredTime', ''),
                        'is_available': j.get('DeviceAvailable', ''),
                        'charge_type': j.get('InternetChargeType', ''),
                        'provider': self.provider
                    }

    def get_qcloud(self):
        self.provider = QCLOUD_NAME

        with FuturesSession(max_workers=MAX_WORKERS) as session:
            futures = []

            for region in QCLOUD_REGION_LIST:
                url = Qcloud.make_url({'Action': 'DescribeInstances', 'Limit': 100, 'Region': region})
                futures.append(session.get(url))

            for f, region in zip(futures, QCLOUD_REGION_LIST):
                r = f.result()
                info = r.json()

                for j in info.get('instanceSet', []):
                    self.data[j.get('instanceId')] = {
                        'instance_id': j.get('instanceId'),
                        'instance_name': j.get('instanceName', ''),
                        'region_id': region,
                        'region_name': QCLOUD_REGION_NAME.get(region, region),
                        'hostname': j.get('HostName', ''),
                        'image_id': j.get('unImgId', ''),
                        'status': QCLOUD_STATUS.get(j.get('status', ''), j.get('status', '')),
                        'inner_ip': j.get('lanIp', ''),
                        'public_ip': (j.get('wanIpSet') or [''])[0],
                        'cpu': j.get('cpu', 0),
                        'memory': j.get('mem', 0) * 1024,
                        'os_name': j.get('os', ''),
                        'os_type': j.get('OSType', 'linux'),
                        'create_time': j.get('createTime', ''),
                        'expired_time': j.get('deadlineTime', ''),
                        'is_available': j.get('DeviceAvailable', 1),
                        'charge_type': QCLOUD_PAYMODE.get(j.get('networkPayMode', ''), ''),
                        'provider': self.provider
                    }

    def get_zcloud(self):
        self.provider = ZCLOUD_NAME

        pool = ThreadPoolExecutor(MAX_WORKERS)
        futures = []

        for region in ZCLOUD_REGION_LIST:
            futures.append(pool.submit(Zcloud.get_instances, region))

        wait(futures)

        for f, region in zip(futures, ZCLOUD_REGION_LIST):
            r = f.result()

            for j in r:
                self.data[j.get('InstanceId')] = {
                    'instance_id': j.get('InstanceId'),
                    'instance_name': '',
                    'region_id': region,
                    'region_name': ZCLOUD_REGION_NAME.get(j.get('Placement', {}).get('AvailabilityZone', '')[:-1], j.get('Placement', {}).get('AvailabilityZone', '')),
                    'hostname': '',
                    'image_id': j.get('ImageId', ''),
                    'status': ZCLOUD_STATUS.get(j.get('State', {}).get('Name'), ''),
                    'inner_ip': j.get('PrivateIpAddress', ''),
                    'public_ip': j.get('PublicIpAddress', ''),
                    'cpu': ZCLOUD_TYPE.get(j.get('InstanceType'), [0])[0],
                    'memory': ZCLOUD_TYPE.get(j.get('InstanceType'), [0])[1] * 1024,
                    'os_name': '',
                    'os_type': 'linux',
                    'create_time': '',
                    'expired_time': '',
                    'is_available': 1,
                    'charge_type': '',
                    'provider': self.provider
                }

    def save(self):
        self.cur = self.db.cursor()

        sql = '''
            SELECT * FROM instance WHERE provider = %s
        '''
        self.cur.execute(sql, self.provider)
        result = self.cur.fetchall()

        self.db_data = self._change_format(result)

        instances_in_db = set(self.db_data.keys())
        instances_latest = set(self.data.keys())

        del_instances = list(instances_in_db - instances_latest)
        add_instances = list(instances_latest - instances_in_db)
        update_instances = list(instances_latest & instances_in_db)

        if del_instances: self._to_del(del_instances)
        if add_instances: self._to_add(add_instances)
        if update_instances: self._to_update(update_instances)

    def _to_del(self, instances):
        for table in ['server', 'instance']:
            sql = 'DELETE FROM ' + table + ' WHERE ' + get_in_formats('instance_id', instances)

            self.cur.execute(sql, instances)

    def _to_add(self, instances):
        for instance in instances:
            keys = self.data[instance].keys()
            values = [self.data[instance][k] for k in keys]

            sql = 'INSERT INTO instance( ' + ','.join(keys) + ')' + ' VALUES ('
            sql += get_formats(values) + ')'

            self.cur.execute(sql, values)

    def _to_update(self, instances):
        real_update = []

        for instance in instances:
            for k, v in self.data[instance].items():
                if v != self.db_data[instance][k]:
                    real_update.append(self.data[instance])
                    break

        for i in real_update:
            s, data = [], []

            for k, v in i.items():
                s.append('{}=%s'.format(k))
                data.append(v)

            data.append(i['instance_id'])

            sql = 'UPDATE instance SET ' + ','.join(s) + ' WHERE instance_id = %s'

            self.cur.execute(sql, data)

    def _change_format(self, result):
        return {i['instance_id']: i for i in result}


def main():
    parser = argparse.ArgumentParser(description='Different clouds')
    parser.add_argument('--cloud', choices=['aliyun', 'qcloud', 'zcloud'], help='which cloud to play')
    args = parser.parse_args()

    obj = Instance()

    cloud_func = {
        'aliyun': obj.get_aliyun,
        'qcloud': obj.get_qcloud,
        'zcloud': obj.get_zcloud
    }

    while True:
        start_time = time.time()
        logging.warning('{:>12}: {}'.format('Start ' + args.cloud, seconds_to_human(start_time)))
        try:
            cloud_func[args.cloud]()

            obj.save()
        except Exception:
            logging.error(traceback.format_exc())
        finally:
            if obj.cur:
                obj.cur.close()

        end_time = time.time()
        logging.warning('{:>12}: {}'.format('End ' + args.cloud, seconds_to_human(end_time)))
        logging.warning('{:>12}: {}s'.format('Cost', end_time - start_time))
        time.sleep(1.5)


if __name__ == '__main__':
    main()