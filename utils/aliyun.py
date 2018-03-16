__author__ = 'Jon'

import uuid
import time
import hashlib
import hmac
import urllib.request, urllib.parse
import base64
import requests
from requests_futures.sessions import FuturesSession
from constant import ALIYUN_DOMAIN, ALIYUN_REGION_LIST

from setting import settings

MAX_WORKERS = 20

class Aliyun:
    domain = ALIYUN_DOMAIN


    #################################################################################################
    # 生成url
    #################################################################################################
    @staticmethod
    def _sign(s):
        h = hmac.new(key=(settings['aliyun_secret'] + '&').encode('utf-8'), digestmod=hashlib.sha1)
        h.update(s.encode('utf-8'))

        return base64.b64encode(h.digest())

    @staticmethod
    def _quote(s):
        return urllib.request.quote(s).replace('%7E', '~').replace('+', '%20').replace('*', '%2A')

    @staticmethod
    def _get_common():
        common = {
            'Format': 'JSON',
            'Version': '2014-05-26',
            'AccessKeyId': settings['aliyun_id'],
            'SignatureMethod': 'HMAC-SHA1',
            'Timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            'SignatureVersion': '1.0',
            'SignatureNonce': str(uuid.uuid1())
        }

        return common

    @classmethod
    def add_sign(cls, params):
        payload = cls._get_common()

        payload.update(params)

        req_str = 'GET&%2F&' + cls._quote('&'.join(['%s=%s' % (cls._quote(k), cls._quote(payload[k])) for k in sorted(payload)]))

        payload.update({'Signature': cls._sign(req_str)})

        return payload

    @classmethod
    def make_url(cls, params=None, domain=None):
        if params is None: params = {}

        if domain is None: domain = cls.domain

        payload = cls.add_sign(params)

        url = domain + urllib.parse.urlencode(payload)

        return url

    #################################################################################################
    # 生成各种命令所需要的参数
    # data 为instance各项属性，
    #################################################################################################
    @classmethod
    def _common(cls, action, data, extra=''):
        cmd = {'Action': action, 'RegionId': data['RegionId'], 'InstanceId': data['InstanceId']}
        if extra:
            arg = {extra: data[extra]}
            cmd.update(arg)
            return cmd
        return cmd

    @classmethod
    def stop(cls, data):
        return cls._common('StopInstance', data)

    @classmethod
    def start(cls, data):
        return cls._common('StartInstance', data)

    @classmethod
    def reboot(cls, data):
        return cls._common('RebootInstance', data)

    @classmethod
    def describe_images(cls, data):
        cmd = cls._common('DescribeImages', data, 'ImageId')
        url = cls.make_url(cmd)
        info = requests.get(url).json()
        images = info['Images']['Image']
        return images

    @classmethod
    def describe_disks(cls, data):
        cmd = cls._common('DescribeDisks', data)
        url = cls.make_url(cmd)
        info = requests.get(url).json()
        disks = info['Disks']['Disk']
        return disks
        # array = []
        # for d in disks:
        #     disk = ''
        #     for i in d:
        #         disk = disk + i+','+str(d[i])
        #     array.append(disk)
        # return array

    @classmethod
    def describe_bandwidth(cls, data):
        cmd = {
            'Action': 'DescribeBandwidthLimitation',
            'RegionId': data['RegionId'],
            'InstanceId': data['InstanceId'],
            'InstanceType': data['InstanceType'],
            'InstanceChargeType': data['InstanceChargeType'],
        }
        url = cls.make_url(cmd)
        info = requests.get(url).json()
        bandwidth = info['Bandwidths']['Bandwidth']
        return bandwidth
        # array = []
        # for d in bandwidth:
        #     tmp = ''
        #     for i in d:
        #         tmp = tmp + i + ',' + str(d[i])
        #     array.append(tmp)
        # return array

    @classmethod
    # get all instances
    def describe_instances(cls):
        instance_urls = []
        instances = []

        for r in ALIYUN_REGION_LIST:
            cmd = {'Action': 'DescribeInstances', 'RegionId': r}
            instance_urls.append(cls.make_url(cmd))

        for url in instance_urls:
            r = requests.get(url).json()
            for j in r['Instances']['Instance']:
                if not j.get('InstanceId', ''):
                    continue
                else:
                    instances.append(j)
        return instances


if __name__ == '__main__':
    instance = Aliyun.describe_instances()
    for i in instance:
        print(Aliyun.describe_images(i))
    # instances = list()
    #
    # for region in ALIYUN_REGION_LIST:
    #     url = Aliyun.make_url({'Action': 'DescribeInstances', 'RegionId': region})
    #
    #     info = requests.get(url, timeout=3).json()
    #
    #     for j in info['Instances']['Instance']:
    #         instances.append(j)
    #
    # from pprint import pprint
    # pprint(instances)