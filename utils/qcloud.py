__author__ = 'Jon'

import sys
import time
import random
import hashlib
import hmac
import urllib.parse
import binascii
import requests
from constant import QCLOUD_DOMAIN, QCLOUD_REGION_LIST, QCLOUD_IMAGE_DOMAIN

from setting import settings

class Qcloud:
    domain = QCLOUD_DOMAIN

    #################################################################################################
    # 生成url
    #################################################################################################
    @staticmethod
    def _sign(s):
        hashed = hmac.new(bytes(settings['qcloud_secret'], 'latin-1'), bytes(s, 'latin-1'), hashlib.sha256)

        return binascii.b2a_base64(hashed.digest())[:-1].decode()

    @staticmethod
    def _get_common():
        common = {
            'SecretId': settings['qcloud_id'],
            'Timestamp': int(time.time()),
            'SignatureMethod': 'HmacSHA256',
            'Nonce': random.randint(1, sys.maxsize),
        }

        return common

    @classmethod
    def add_sign(cls, params, domain=None):

        if domain is None: domain = cls.domain

        payload = cls._get_common()

        payload.update(params)

        req_str = 'GET' + domain[8:-1] + '?' + "&".join(k.replace("_",".") + "=" + str(payload[k]) for k in sorted(payload.keys()))
        payload.update({'Signature': cls._sign(req_str)})

        return payload


    @classmethod
    def make_url(cls, params=None, domain=None):
        if params is None: params = {}

        if domain is None: domain = cls.domain

        payload = cls.add_sign(params, domain)

        url = domain + urllib.parse.urlencode(payload)
        return url

    #################################################################################################
    # 生成各种命令所需要的参数
    #################################################################################################
    @classmethod
    def _common(cls, action, data):
        return {'Action': action, 'InstanceIds.0': data['instance_id'], 'Region': data['region_id'], 'Version': '2017-03-12'}

    @classmethod
    def stop(cls, data):
        return cls._common('StopInstances', data)

    @classmethod
    def start(cls, data):
        return cls._common('StartInstances', data)

    @classmethod
    def reboot(cls, data):
        return cls._common('RestartInstances', data)

    @classmethod
    def describe_instances(cls):
        qcloud_instances = []

        for r in QCLOUD_REGION_LIST:
            cmd = {'Action': 'DescribeInstances', 'Limit': 100, 'Region': r, 'Version': '2017-03-12'}
            instance_url = cls.make_url(cmd)

            result = requests.get(instance_url).json()

            if not result['Response'].get('InstanceSet', ''):
                continue

            for one in result['Response']['InstanceSet']:
                    one.update({'region_id': r})
                    qcloud_instances.append(one)
        return qcloud_instances

    @classmethod
    def instance_status(cls, data):
        cmd = {
            'Action': 'DescribeInstancesStatus',
            'InstanceIds.0': data['InstanceId'],
            'Region': data['region_id'],
            'Version': '2017-03-12'
        }
        status_url = cls.make_url(cmd)
        status_info = requests.get(status_url).json()
        return status_info['Response']['InstanceStatusSet'][0]['InstanceState']

    @classmethod
    def describe_images(cls, data):
        cmd = {
            'Action': 'DescribeImages',
            'Version': '2017-03-12',
            'ImageIds.1': data['ImageId'],
            'Region': data['region_id']
        }
        image_url = cls.make_url(params=cmd, domain=QCLOUD_IMAGE_DOMAIN)
        image_info = requests.get(image_url).json()
        images = image_info['Response']['ImageSet']

        resp = list()
        if not len(images):
            return resp

        for one in images:
            image = dict()
            image['ImageId'] = one['ImageId']
            image['ImageVersion'] = ''
            image['OSType'] = ''
            image['Platform'] = one['Platform']
            image['Architecture'] = one['Architecture']
            image['ImageName'] = one['ImageName']
            image['Size'] = one['ImageSize']
            image['OSName'] = one['OsName']
            resp.append(image)
        return resp


if __name__ == '__main__':
    instances = list()

    for region in QCLOUD_REGION_LIST:
        url = Qcloud.make_url({'Action': 'DescribeInstances', 'Limit': 100, 'Region': region, 'Version': '2017-03-12'})
        info = requests.get(url, timeout=3).json()

        for j in info.get('Response').get('InstanceSet', []):
            instances.append(j)

    from pprint import pprint
    pprint(instances)

    # url = Qcloud.make_url({'Action': 'RestartInstances', 'instanceIds.0': 'qcvm89c880fbaf392972dbb536cd55d0d99d', 'Region': 'ap-guangzhou'})
    # pprint(url)
    # info = requests.get(url, timeout=3).json()
    # pprint(info)