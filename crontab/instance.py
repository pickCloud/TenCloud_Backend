__author__ = 'Jon'

'''获取阿里云的实例,并更新数据库
'''
import json
import time
from tornado.ioloop import IOLoop
from tornado.gen import coroutine
from tornado.httpclient import AsyncHTTPClient
from utils.aliyun import Aliyun
from utils.db import DB
from constant import ALIYUN_REGION_LIST, HTTP_TIMEOUT

class Instance:
    def __init__(self):
        self.data = []
        self.db = DB
        self.instance_num = 0

    @coroutine
    def get(self):
        for region in ALIYUN_REGION_LIST:
            url = Aliyun.make_url({'Action': 'DescribeInstances', 'RegionId': region})

            res = yield AsyncHTTPClient().fetch(url, request_timeout=HTTP_TIMEOUT)
            info = json.loads(res.body.decode())

            for j in info['Instances']['Instance']:
                self.data.extend([j.get('InstanceId'),
                                  j.get('InstanceName', ''),
                                  j.get('RegionId'),
                                  j.get('HostName', ''),
                                  j.get('ImageId', ''),
                                  j.get('Status', ''),
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
                                  'aliyun'])
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
    obj = Instance()

    while True:
        yield obj.get()
        yield obj.save()
        time.sleep(1)


if __name__ == '__main__':
    IOLoop.current().run_sync(main)