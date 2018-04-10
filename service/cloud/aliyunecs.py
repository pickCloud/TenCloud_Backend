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


class AliyunBase:
    def __init__(self, access_key_id, access_key_secret):
        self.aliyun_domain = ''
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    #################################################################################################
    # 生成url
    #################################################################################################
    def _sign(self, s):
        h = hmac.new(key=(self.access_key_secret + '&').encode('utf-8'), digestmod=hashlib.sha1)
        h.update(s.encode('utf-8'))
        return base64.b64encode(h.digest())

    @staticmethod
    def _quote(s):
        return urllib.request.quote(s).replace('%7E', '~').replace('+', '%20').replace('*', '%2A')

    def _get_common(self):
        common = {
            'Format': 'JSON',
            'Version': '2014-05-26',
            'AccessKeyId': self.access_key_id,
            'SignatureMethod': 'HMAC-SHA1',
            'Timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            'SignatureVersion': '1.0',
            'SignatureNonce': str(uuid.uuid1())
        }
        return common

    def add_sign(self, params):
        payload = self._get_common()

        payload.update(params)

        req_str = 'GET&%2F&' + self._quote('&'.join(['%s=%s' % (self._quote(k), self._quote(payload[k])) for k in sorted(payload)]))

        payload.update({'Signature': self._sign(req_str)})

        return payload

    def make_url(self, params=None, aliyun_domain=None):
        if params is None:
            params = {}

        if aliyun_domain is None:
            aliyun_domain = self.aliyun_domain

        payload = self.add_sign(params)

        url = aliyun_domain + urllib.parse.urlencode(payload)

        return url


class AliyunECSBase(AliyunBase):
    def __init__(self, access_key_id, access_key_secret, ecs_domain):
        super().__init__(access_key_id, access_key_secret)
        self.aliyun_domain = ecs_domain

    def get_all_region_instance(self):
        all_region_instances = list()
        for r in ALIYUN_REGION_LIST:
            cmd = {'Action': 'DescribeInstances', 'RegionId': r}
            url = self.make_url(cmd)
            r = requests.get(url).json()
            if not r.get('Instances', {}).get('Instance', ''):
                continue
            for j in r['Instances']['Instance']:
                j.update({'region_id': j['RegionId']})
                all_region_instances.append(j)
        return all_region_instances


