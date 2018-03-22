__author__ = 'Jon'

'''获取各种云的实例,并更新数据库
'''
import sys
import argparse
import time
import traceback
import logging
import json

logging.basicConfig(stream=sys.stdout, level=logging.WARN)

import pymysql.cursors
from utils.aliyun import Aliyun
from utils.qcloud import Qcloud
from utils.zcloud import Zcloud
from utils.datetool import seconds_to_human
from utils.general import get_formats, get_in_formats
from constant import ALIYUN_NAME, QCLOUD_NAME, ALIYUN_REGION_NAME, QCLOUD_REGION_NAME, ZCLOUD_REGION_LIST, \
    ZCLOUD_TYPE, ZCLOUD_NAME, ZCLOUD_REGION_NAME, TCLOUD_STATUS_MAKER, TCLOUD_STATUS
from setting import settings
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
            status = TCLOUD_STATUS_MAKER.get(i.get('Status', ''), i.get('Status', ''))
            self.data[i.get('InstanceId')]= {
                'instance_id': i.get('InstanceId'),
                'instance_name': i.get('InstanceName', ''),
                'region_id': i.get('RegionId', ''),
                'region_name': ALIYUN_REGION_NAME.get(i.get('RegionId', ''), i.get('RegionId', '')),
                'hostname': i.get('HostName', ''),
                'status': TCLOUD_STATUS.get(status, status),

                'inner_ip': ','.join(i['InnerIpAddress']['IpAddress']) if len(i['InnerIpAddress']['IpAddress']) else '',
                'public_ip': ','.join(i['PublicIpAddress']['IpAddress']) if len(i['PublicIpAddress']['IpAddress']) else '',
                'security_group_ids': ','.join(i['SecurityGroupIds']['SecurityGroupId']) if len(i['SecurityGroupIds']['SecurityGroupId'])else '',

                'cpu': i.get('Cpu', 0),
                'memory': i.get('Memory', 0),
                'os_name': i.get('OSName', ''),
                'os_type': i.get('OSType', ''),
                'create_time': i.get('CreationTime', ''),
                'expired_time': i.get('ExpiredTime', ''),
                'is_available': i.get('DeviceAvailable', ''),
                'charge_type': i.get('InternetChargeType', ''),
                'provider': self.provider,
                'instance_network_type': i.get('InstanceNetworkType', ''),
                'internet_max_bandwidth_in': str(i.get('InternetMaxBandwidthIn', ''))+"Mbps",
                'internet_max_bandwidth_out': str(i.get('InternetMaxBandwidthOut', ''))+"Mbps",

                'disk_info': json.dumps(disks),
                'image_info': json.dumps(images)
            }

    def get_qcloud(self):
        self.provider = QCLOUD_NAME

        instances = Qcloud.describe_instances()
        for i in instances:
            status = TCLOUD_STATUS_MAKER.get(Qcloud.instance_status(i))
            disks = [
                {
                    'DiskType': i.get('SystemDisk', {}).get('DiskType'),
                    'DiskId': i.get('SystemDisk', {}).get('DiskId'),
                    'DiskSize': i.get('SystemDisk', {}).get('DiskSize', ''),
                    'DiskCategory': 'system'
                }
            ]
            if i.get('DataDisks') is not None:
                for d in i.get('DataDisks', []):
                    d.update({'DiskCategory': 'data'})
                    disks.append(d)
            images = Qcloud.describe_images(i)

            self.data[i['InstanceId']] = {
                'instance_id': i.get('InstanceId'),
                'instance_name': i.get('InstanceName'),
                'region_id': i['region_id'],
                'region_name': QCLOUD_REGION_NAME.get(i['region_id'], i['region_id']),
                'hostname': i.get('HostName'),
                'image_id': i.get('ImageId'),
                'status': TCLOUD_STATUS.get(status, status),

                'inner_ip': ','.join(i.get('PrivateIpAddresses')) if len(i.get('PrivateIpAddresses')) else '',
                'public_ip': ','.join(i.get('PublicIpAddresses')) if len(i.get('PublicIpAddresses')) else '',
                'security_group_ids': ','.join(i.get('SecurityGroupIds', [])),

                'cpu': i.get('CPU', 0),
                'memory': i.get('Memory', 0) * 1024,
                'os_name': i.get('OsName', ''),
                'os_type': i.get('OSType', 'linux'),
                'create_time': i.get('CreatedTime', ''),
                'expired_time': i.get('ExpiredTime', ''),
                'is_available': i.get('DeviceAvailable', 1),
                'charge_type': i.get('InternetAccessible', {}).get('InternetChargeType', ''),
                'provider': self.provider,
                'instance_network_type': 'vpc',
                'internet_max_bandwidth_in': '',
                'internet_max_bandwidth_out': str(
                    i.get('InternetAccessible', {}).get('InternetMaxBandwidthOut', '')) + "Mbps",

                'disk_info': json.dumps(disks),
                'image_info': json.dumps(images)

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
                status = TCLOUD_STATUS_MAKER.get(j.get('State', {}).get('Name'), '')
                images = Zcloud.describe_image({'region_id': region, 'ImageId': j.get('ImageId', '')})
                disks = Zcloud.describe_disk({'region_id': region})

                self.data[j.get('InstanceId')] = {
                    'instance_id': j.get('InstanceId'),
                    'instance_name': '',
                    'region_id': region,
                    'region_name': ZCLOUD_REGION_NAME.get(j.get('Placement', {}).get('AvailabilityZone', '')[:-1], j.get('Placement', {}).get('AvailabilityZone', '')),
                    'hostname': '',
                    'image_id': j.get('ImageId', ''),
                    'status': TCLOUD_STATUS.get(status, status),
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
                    'security_group_ids': ','.join([i['GroupId'] for i in j.get('SecurityGroups', '')]),
                    'instance_network_type': 'vpc',
                    'internet_max_bandwidth_in': '',
                    'internet_max_bandwidth_out': '',


                    'image_info': json.dumps(images),
                    'disk_info': json.dumps(disks)
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