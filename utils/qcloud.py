__author__ = 'Jon'

import sys
import time
import random
import hashlib
import hmac
import urllib.parse
import binascii
import requests
from constant import QCLOUD_DOMAIN, QCLOUD_HOST, QCLOUD_REGION_LIST

from setting import settings

class Qcloud:
    domain = QCLOUD_DOMAIN

    @staticmethod
    def _sign(s):
        hashed = hmac.new(bytes(settings['qcloud_secret'], 'latin-1'), bytes(s, 'latin-1'), hashlib.sha1)

        return binascii.b2a_base64(hashed.digest())[:-1].decode()

    @staticmethod
    def _get_common():
        common = {
            'SecretId': settings['qcloud_id'],
            'SignatureMethod': 'HmacSHA1',
            'Timestamp': int(time.time()),
            'Nonce': random.randint(1, sys.maxsize),
        }

        return common

    @classmethod
    def add_sign(cls, params):
        payload = cls._get_common()

        payload.update(params)

        req_str = 'GET' + QCLOUD_HOST + '?' + "&".join(k.replace("_",".") + "=" + str(payload[k]) for k in sorted(payload.keys()))

        payload.update({'Signature': cls._sign(req_str)})

        return payload


    @classmethod
    def make_url(cls, params=None, domain=None):
        if params is None: params = {}

        if domain is None: domain = cls.domain

        payload = cls.add_sign(params)

        url = domain + urllib.parse.urlencode(payload)

        return url


if __name__ == '__main__':
    instances = list()

    for region in QCLOUD_REGION_LIST:
        url = Qcloud.make_url({'Action': 'DescribeInstances', 'Limit': 100, 'Region': region})
        info = requests.get(url, timeout=3).json()

        for j in info.get('instanceSet', []):
            instances.append(j)

    from pprint import pprint
    pprint(instances)