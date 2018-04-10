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

class QcloudBase:

    def __init__(self, access_key_id, access_key_secret):
        self.qcloud_domain = ''
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    #################################################################################################
    # 生成url
    #################################################################################################
    def _sign(self, s):
        # hashed = hmac.new(bytes(settings['qcloud_secret'], 'latin-1'), bytes(s, 'latin-1'), hashlib.sha256)
        hashed = hmac.new(bytes(self.access_key_secret, 'latin-1'), bytes(s, 'latin-1'), hashlib.sha256)

        return binascii.b2a_base64(hashed.digest())[:-1].decode()

    def _get_common(self):
        common = {
            'SecretId': self.access_key_id,
            'Timestamp': int(time.time()),
            'SignatureMethod': 'HmacSHA256',
            'Nonce': random.randint(1, sys.maxsize),
        }

        return common

    def add_sign(self, params, qcloud_domain=None):

        if qcloud_domain is None: qcloud_domain = self.qcloud_domain

        payload = self._get_common()

        payload.update(params)

        req_str = 'GET' + qcloud_domain[8:-1] + '?' + "&".join(k.replace("_", ".") + "=" + str(payload[k]) for k in sorted(payload.keys()))
        payload.update({'Signature': self._sign(req_str)})

        return payload

    def make_url(self, params=None, qcloud_domain=None):
        if params is None: params = {}

        if qcloud_domain is None: qcloud_domain = self.qcloud_domain

        payload = self.add_sign(params, qcloud_domain)

        url = qcloud_domain + urllib.parse.urlencode(payload)
        return url

class QcloudCVMBase(QcloudBase):
    def __init__(self, access_key_id, access_key_secret, cvm_domain):
        super().__init__(access_key_id, access_key_secret)
        self.qcloud_domain = cvm_domain

    def get_all_region_instance(self):
        all_region_instances = list()
        for r in QCLOUD_REGION_LIST:
            cmd = {'Action': 'DescribeInstances', 'Limit': 100, 'Region': r, 'Version': '2017-03-12'}
            url = self.make_url(cmd)
            result = requests.get(url).json()
            if not result['Response'].get('InstanceSet', ''):
                continue
            for one in result['Response']['InstanceSet']:
                one.update({'region_id': r})
                all_region_instances.append(one)
        return all_region_instances


# if __name__ == '__main__':

    # url = Qcloud.make_url({'Action': 'RestartInstances', 'instanceIds.0': 'qcvm89c880fbaf392972dbb536cd55d0d99d', 'Region': 'ap-guangzhou'})
    # pprint(url)
    # info = requests.get(url, timeout=3).json()
    # pprint(info)