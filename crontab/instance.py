__author__ = 'Jon'

'''获取阿里云的实例,并更新数据库
'''
import sys
import argparse
import json
import time
import logging
logging.basicConfig(stream=sys.stdout, level=logging.WARN)

from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado_mysql import pools, cursors
from utils.aliyun import Aliyun
from utils.qcloud import Qcloud
from utils.zcloud import Zcloud
from utils.datetool import seconds_to_human
from constant import ALIYUN_REGION_LIST, HTTP_TIMEOUT, QCLOUD_REGION_LIST, QCLOUD_STATUS, QCLOUD_PAYMODE, ALIYUN_NAME, \
                     QCLOUD_NAME, ALIYUN_REGION_NAME, QCLOUD_REGION_NAME, ALIYUN_STATUS, ZCLOUD_REGION_LIST, ZCLOUD_STATUS, \
                     ZCLOUD_TYPE, ZCLOUD_NAME, ZCLOUD_REGION_NAME
from setting import settings

DB = pools.Pool(
        dict(host=settings['mysql_host'],
             port=settings['mysql_port'],
             user=settings['mysql_user'],
             passwd=settings['mysql_password'],
             db=settings['mysql_database'],
             cursorclass=cursors.DictCursor,
             charset=settings['mysql_charset']),
        max_idle_connections=1,
        max_recycle_sec=120
     )

class Instance:
    def __init__(self):
        self.data = []
        self.db = DB
        self.instance_num = 0

    @coroutine
    def get_aliyun(self):
        for region in ALIYUN_REGION_LIST:
            url = Aliyun.make_url({'Action': 'DescribeInstances', 'RegionId': region})

            res = yield AsyncHTTPClient().fetch(url, request_timeout=HTTP_TIMEOUT)
            info = json.loads(res.body.decode())

            for j in info['Instances']['Instance']:
                self.data.extend([j.get('InstanceId'),
                                  j.get('InstanceName', ''),
                                  ALIYUN_REGION_NAME.get(j.get('RegionId', ''), j.get('RegionId', '')),
                                  j.get('HostName', ''),
                                  j.get('ImageId', ''),
                                  ALIYUN_STATUS.get(j.get('Status', ''), j.get('Status', '')),
                                  (j.get('InnerIpAddress', {}).get('IpAddress') or [''])[0],
                                  (j.get('PublicIpAddress', {}).get('IpAddress') or [''])[0],
                                  j.get('Cpu', 0),
                                  j.get('Memory', 0),
                                  j.get('OSName', ''),
                                  j.get('OSType', ''),
                                  j.get('CreationTime', ''),
                                  j.get('ExpiredTime', ''),
                                  j.get('DeviceAvailable', ''),
                                  j.get('InternetChargeType', ''),
                                  ALIYUN_NAME])
                self.instance_num += 1

    @coroutine
    def get_qcloud(self):
        for region in QCLOUD_REGION_LIST:
            url = Qcloud.make_url({'Action': 'DescribeInstances', 'Limit': 100, 'Region': region})

            res = yield AsyncHTTPClient().fetch(url, request_timeout=HTTP_TIMEOUT)
            info = json.loads(res.body.decode())

            for j in info.get('instanceSet', []):
                self.data.extend([j.get('instanceId'),
                                  j.get('instanceName', ''),
                                  QCLOUD_REGION_NAME.get(region, region),
                                  j.get('HostName', ''),
                                  j.get('unImgId', ''),
                                  QCLOUD_STATUS.get(j.get('status', ''), j.get('status', '')),
                                  j.get('lanIp', ''),
                                  (j.get('wanIpSet') or [''])[0],
                                  j.get('cpu', 0),
                                  j.get('mem', 0) * 1024,
                                  j.get('os', ''),
                                  j.get('OSType', 'linux'),
                                  j.get('createTime', ''),
                                  j.get('deadlineTime', ''),
                                  j.get('DeviceAvailable', 1),
                                  QCLOUD_PAYMODE.get(j.get('networkPayMode', ''), ''),
                                  QCLOUD_NAME])
                self.instance_num += 1

    @coroutine
    def get_zcloud(self):
        for region in ZCLOUD_REGION_LIST:
            instances = Zcloud.get_instances(region)

            for j in instances:
                self.data.extend([j.get('InstanceId'),
                                  '',
                                  ZCLOUD_REGION_NAME.get(j.get('Placement', {}).get('AvailabilityZone', '')[:-1], j.get('Placement', {}).get('AvailabilityZone', '')),
                                  '',
                                  j.get('ImageId', ''),
                                  ZCLOUD_STATUS.get(j.get('State', {}).get('Name'), ''),
                                  j.get('PrivateIpAddress', ''),
                                  j.get('PublicIpAddress', ''),
                                  ZCLOUD_TYPE.get(j.get('InstanceType'), [0])[0],
                                  ZCLOUD_TYPE.get(j.get('InstanceType'), [0])[1] * 1024,
                                  '',
                                  'linux',
                                  '',
                                  '',
                                  1,
                                  '',
                                  ZCLOUD_NAME
                                  ])
                self.instance_num += 1


    @coroutine
    def save(self):
        sql = " INSERT INTO instance(instance_id, instance_name, region_id, hostname, image_id, status, inner_ip," \
              " public_ip, cpu, memory, os_name, os_type, create_time, expired_time, is_available, charge_type, provider) " \
              " VALUES "

        sql += ",".join("(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" for _ in range(self.instance_num))

        sql += " ON DUPLICATE KEY UPDATE instance_name=VALUES(instance_name), " \
               "                         region_id=VALUES(region_id)," \
               "                         hostname=VALUES(hostname), " \
               "                         image_id=VALUES(image_id), " \
               "                         status=VALUES(status), " \
               "                         inner_ip=VALUES(inner_ip), " \
               "                         public_ip=VALUES(public_ip), " \
               "                         cpu=VALUES(cpu), " \
               "                         memory=VALUES(memory)," \
               "                         os_name=VALUES(os_name), " \
               "                         os_type=VALUES(os_type), " \
               "                         create_time=VALUES(create_time), " \
               "                         expired_time=VALUES(expired_time), " \
               "                         is_available=VALUES(is_available), " \
               "                         charge_type=VALUES(charge_type)"

        yield self.db.execute(sql, self.data)

@coroutine
def main():
    parser = argparse.ArgumentParser(description='Different clouds')
    parser.add_argument('--cloud', choices=['aliyun', 'qcloud', 'zcloud'], help='which cloud to play')
    args = parser.parse_args()

    obj = Instance()

    while True:
        start_time = time.time()
        logging.warning('{:>12}: {}'.format('Start ' + args.cloud, seconds_to_human(start_time)))
        try:
            if args.cloud == 'aliyun':
                yield obj.get_aliyun()
            elif args.cloud == 'qcloud':
                yield obj.get_qcloud()
            elif args.cloud == 'zcloud':
                yield obj.get_zcloud()

            yield obj.save()
        except HTTPError as e:
            err = 'STATUS: {status}, BODY: {body}, URL: {url}'.format(status=str(e), body=e.response.body,
                                                                      url=e.response.effective_url)
            print(err)
        except Exception as e:
            print(e)
        end_time = time.time()
        logging.warning('{:>12}: {}'.format('End ' + args.cloud, seconds_to_human(end_time)))
        logging.warning('{:>12}: {}s'.format('Cost ', end_time - start_time))
        time.sleep(1)



if __name__ == '__main__':
    IOLoop.current().run_sync(main)