__author__ = 'Jon'

import uuid
import time
import hashlib
import hmac
import urllib.request, urllib.parse
import base64
import requests
from constant import ALIYUN_DOMAIN

from setting import settings

class Aliyun:
    domain = ALIYUN_DOMAIN

    @staticmethod
    def _sign(query):
        s = 'GET&%2F&' + query

        h = hmac.new(key=(settings['aliyun_secret'] + '&').encode('utf-8'), digestmod=hashlib.sha1)
        h.update(s.encode('utf-8'))

        return base64.b64encode(h.digest())

    @staticmethod
    def _quote(s):
        return urllib.request.quote(s).replace('%7E', '~').replace('+', '%20').replace('*', '%2A')

    @classmethod
    def add_sign(cls, params):
        payload = {
            'Format': 'JSON',
            'Version': '2014-05-26',
            'AccessKeyId': settings['aliyun_id'],
            'SignatureMethod': 'HMAC-SHA1',
            'Timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            'SignatureVersion': '1.0',
            'SignatureNonce': str(uuid.uuid1())
        }
        payload.update(params)

        query = cls._quote('&'.join(['%s=%s' % (cls._quote(k), cls._quote(payload[k])) for k in sorted(payload)]))

        payload.update({'Signature': cls._sign(query)})

        return payload

    @classmethod
    def make_url(cls, params=None, domain=None):
        if params is None: params = {}

        if domain is None: domain = cls.domain

        payload = cls.add_sign(params)

        url = domain + urllib.parse.urlencode(payload)

        return url


if __name__ == '__main__':
    region_list = ['cn-qingdao', 'cn-beijing', 'cn-zhangjiakou', 'cn-hangzhou', 'cn-shanghai', 'cn-shenzhen',
                   'cn-hongkong', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'us-west-1', 'us-east-1',
                   'eu-central-1', 'me-east-1']

    instances = list()
    for region in region_list:
        url = Aliyun.make_url({'Action': 'DescribeInstances', 'RegionId': region})

        info = requests.get(url).json()

        for j in info['Instances']['Instance']:
            instances.append(j)

    from pprint import pprint
    pprint(instances)
    #
    # instance_id = 'i-uf6iq9x2bup1zli6hs9u'
    #
    # url = Aliyun.make_url({'Action': 'StartInstance', 'InstanceId': instance_id})
    # print(requests.get(url).json())