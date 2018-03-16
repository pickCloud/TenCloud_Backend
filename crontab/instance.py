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
    ZCLOUD_TYPE, ZCLOUD_NAME, ZCLOUD_REGION_NAME, TCLOUD_STATUS_MAKER
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

        instances = Aliyun.describe_instances()
        if not len(instances):
            return
        for i in instances:
            disks = Aliyun.describe_disks(i)
            images = Aliyun.describe_images(i)
            status = ALIYUN_STATUS.get(i.get('Status', ''), i.get('Status', ''))
            self.data[i.get('InstanceId')]= {
                'instance_id': i.get('InstanceId'),
                'instance_name': i.get('InstanceName', ''),
                'region_id': i.get('RegionId', ''),
                'region_name': ALIYUN_REGION_NAME.get(i.get('RegionId', ''), i.get('RegionId', '')),
                'hostname': i.get('HostName', ''),

                'image_id': images[0]['ImageId'] if len(images) else '',
                'image_name': images[0]['ImageName'] if len(images) else '',
                'image_version': images[0]['ImageVersion'] if len(images) else '' ,

                'status': TCLOUD_STATUS_MAKER.get(status, status),
                'inner_ip': (i.get('InnerIpAddress', {}).get('IpAddress') or [''])[0],
                'public_ip': (i.get('PublicIpAddress', {}).get('IpAddress') or [''])[0],
                'cpu': i.get('Cpu', 0),
                'memory': i.get('Memory', 0),
                'os_name': i.get('OSName', ''),
                'os_type': i.get('OSType', ''),
                'create_time': i.get('CreationTime', ''),
                'expired_time': i.get('ExpiredTime', ''),
                'is_available': i.get('DeviceAvailable', ''),
                'charge_type': i.get('InternetChargeType', ''),
                'provider': self.provider,
                'security_group_ids': i.get('SecurityGroupIds', '').get('SecurityGroupId', []),
                'instance_network_type': i.get('InstanceNetworkType', ''),
                'internet_max_bandwidth_in': str(i.get('InternetMaxBandwidthIn', ''))+"Mbps",
                'internet_max_bandwidth_out': str(i.get('InternetMaxBandwidthOut', ''))+"Mbps",

                'system_disk_size': str(disks[0]['Size'])+'G' if len(disks) else '',
                'system_disk_id': disks[0]['DiskId'] if len(disks) else '',
                'system_disk_type': disks[0]['Category'] if len(disks) else '',
            }
            # for f in instances:
            #     r = f.result()
            #     info = r.json()
            #
            #     for j in info['Instances']['Instance']:
            #         status = ALIYUN_STATUS.get(j.get('Status', ''), j.get('Status', ''))
            #
            #         disk_size, disk_type = Instance.get_disk(j.get('ImageId', ''))
            #         self.data[j.get('InstanceId')] = {
            #             'instance_id': j.get('InstanceId'),
            #             'instance_name': j.get('InstanceName', ''),
            #             'region_id': j.get('RegionId', ''),
            #             'region_name': ALIYUN_REGION_NAME.get(j.get('RegionId', ''), j.get('RegionId', '')),
            #             'hostname': j.get('HostName', ''),
            #
            #             'image_id': j.get('ImageId', ''),
            #             'image_name': '',
            #             'image_version': '',
            #
            #             'status': TCLOUD_STATUS_MAKER.get(status, status),
            #             'inner_ip': (j.get('InnerIpAddress', {}).get('IpAddress') or [''])[0],
            #             'public_ip': (j.get('PublicIpAddress', {}).get('IpAddress') or [''])[0],
            #             'cpu': j.get('Cpu', 0),
            #             'memory': j.get('Memory', 0),
            #             'os_name': j.get('OSName', ''),
            #             'os_type': j.get('OSType', ''),
            #             'create_time': j.get('CreationTime', ''),
            #             'expired_time': j.get('ExpiredTime', ''),
            #             'is_available': j.get('DeviceAvailable', ''),
            #             'charge_type': j.get('InternetChargeType', ''),
            #             'provider': self.provider,
            #             'security_group_ids': j.get('SecurityGroupIds', '').get('SecurityGroupId', []),
            #             'instance_network_type': j.get('InstanceNetworkType', ''),
            #             'internet_max_bandwidth_in': j.get('InternetMaxBandwidthIn', ''),
            #             'internet_max_bandwidth_out': j.get('InternetMaxBandwidthOut', ''),
            #
            #             'system_disk_size': disk_size,
            #             'system_disk_id': j.get('SystemDisk', {}).get('DiskId', ''),
            #             'system_disk_type': disk_type,
            #         }

    def get_qcloud(self):
        self.provider = QCLOUD_NAME

        with FuturesSession(max_workers=MAX_WORKERS) as session:
            futures = []

            for region in QCLOUD_REGION_LIST:
                url = Qcloud.make_url({'Action': 'DescribeInstances', 'Limit': 100, 'Region': region, 'Version': '2017-03-12'})
                futures.append(session.get(url))

            for f, region in zip(futures, QCLOUD_REGION_LIST):
                r = f.result()
                info = r.json()

                for j in info.get('Response', {}).get('InstanceSet', []):
                    status = QCLOUD_STATUS.get(j.get('status', ''), j.get('status', ''))
                    self.data[j.get('InstanceId')] = {
                        'instance_id': j.get('InstanceId'),
                        'instance_name': j.get('InstanceName', ''),
                        'region_id': region,
                        'region_name': QCLOUD_REGION_NAME.get(region, region),
                        'hostname': j.get('HostName', ''),
                        'image_id': j.get('ImageId', ''),
                        'status': TCLOUD_STATUS_MAKER.get(status, status),
                        'inner_ip': j.get('PrivateIpAddresses', ''),
                        'public_ip': j.get('PublicIpAddresses', ''),
                        'cpu': j.get('CPU', 0),
                        'memory': j.get('Memory', 0) * 1024,
                        'os_name': j.get('OsName', ''),
                        'os_type': j.get('OSType', 'linux'),
                        'create_time': j.get('CreatedTime', ''),
                        'expired_time': j.get('ExpiredTime', ''),
                        'is_available': j.get('DeviceAvailable', 1),
                        'charge_type': j.get('InternetAccessible', {}).get('InternetChargeType', ''),
                        'provider': self.provider,
                        'security_group_ids': '.'.join(j.get('SecurityGroupIds', [])),
                        'instance_network_type': 'vpc',
                        'internet_max_bandwidth_in': '',
                        'internet_max_bandwidth_out': str(j.get('InternetAccessible', {}).get('InternetMaxBandwidthOut', ''))+"Mbps",
                        'system_disk_size': j.get('SystemDisk', {}).get('DiskSize', ''),
                        'system_disk_id': j.get('SystemDisk', {}).get('DiskId', ''),
                        'system_disk_type': j.get('SystemDisk', {}).get('DiskType', ''),
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
                status = ZCLOUD_STATUS.get(j.get('State', {}).get('Name'), '')

                self.data[j.get('InstanceId')] = {
                    'instance_id': j.get('InstanceId'),
                    'instance_name': '',
                    'region_id': region,
                    'region_name': ZCLOUD_REGION_NAME.get(j.get('Placement', {}).get('AvailabilityZone', '')[:-1], j.get('Placement', {}).get('AvailabilityZone', '')),
                    'hostname': '',
                    'image_id': j.get('ImageId', ''),
                    'status': TCLOUD_STATUS_MAKER.get(status, status),
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
                    'provider': self.provider,
                    'security_group_ids': [i['GroupId'] for i in j.get('SecurityGroups', '')],
                    'instance_network_type': 'vpc',
                    'internet_max_bandwidth_in': '',
                    'internet_max_bandwidth_out': '',
                    'system_disk_size': '',
                    'system_disk_id': '',
                    'system_disk_type': '',
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