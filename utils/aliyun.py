__author__ = 'Jon'

import uuid
import time
import hashlib
import hmac
import urllib.request, urllib.parse
import base64
import requests
import json
from constant import ALIYUN_DOMAIN, ALIYUN_REGION_LIST, ALIYUN_DISK_TYPE

from setting import settings


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
        return {'Action': action, 'RegionId': data['region_id'], 'InstanceId': data['instance_id']}

    @classmethod
    def stop(cls, data):
        return cls._common('StopInstance', data)

    @classmethod
    def start(cls, data):
        return cls._common('StartInstance', data)

    @classmethod
    def reboot(cls, data):
        return cls._common('RebootInstance', data)

    # 如果获取到空数据，很大原因是改image已被销毁，目前所有image中含有base的都已被阿里销毁
    @classmethod
    def describe_images(cls, data):
        cmd = {
            'Action': 'DescribeImages',
            'RegionId': data['region_id'],
            'InstanceId': data['InstanceId']
        }
        if data.get('ImageId', ''):
            cmd.update({'ImageId': data['ImageId']})

        url = cls.make_url(cmd)
        info = requests.get(url).json()
        images = info['Images']['Image']

        resp = list()
        if not len(images):
            return resp

        for one in images:
            image = dict()
            image['ImageId'] = one['ImageId']
            image['ImageVersion'] = one['ImageVersion']
            image['OSType'] = one['OSType']
            image['Platform'] = one['Platform']
            image['Architecture'] = one['Architecture']
            image['ImageName'] = one['ImageName']
            image['Size'] = one['Size']
            image['OSName'] = one['OSName']
            resp.append(image)
        return resp

    # 提取disk信息，并返回其数组
    @classmethod
    def describe_disks(cls, data):
        cmd = {
            'Action': 'DescribeDisks',
            'RegionId': data['region_id'],
            'InstanceId': data['InstanceId']
        }
        url = cls.make_url(cmd)
        info = requests.get(url).json()
        disks = info['Disks']['Disk']

        resp = list()
        if not len(disks):
            return resp

        for one in disks:
            disk = dict()
            category = one['Category']
            disk['DiskId'] = one['DiskId']
            disk['DiskName'] = one['DiskName']
            disk['DiskType'] = one['Type']
            disk['DiskCategory'] = ALIYUN_DISK_TYPE.get(category, category)
            disk['DiskSize'] = one['Size']
            disk['InstanceId'] = one['InstanceId']
            disk['Device'] = one['Device']
            resp.append(disk)
        return resp

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

    # get all instances
    @classmethod
    def describe_instances(cls):
        instance_urls = []
        instances = []

        for r in ALIYUN_REGION_LIST:
            cmd = {'Action': 'DescribeInstances', 'RegionId': r}
            instance_urls.append(cls.make_url(cmd))

        for url in instance_urls:
            r = requests.get(url).json()

            if not r['Instances'].get('Instance', ''):
                continue

            for j in r['Instances']['Instance']:
                j.update({'region_id': j['RegionId']})
                instances.append(j)
        return instances


if __name__ == '__main__':
    instance = Aliyun.describe_instances()
    for i in instance:
        ret = json.dumps(Aliyun.describe_disks(i))
        print(ret)
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