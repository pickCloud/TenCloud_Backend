__author__ = 'Jon'


import boto3
from constant import ZCLOUD_REGION_LIST

from setting import settings


class Zcloud:
    service = 'ec2'

    @classmethod
    def get_instances(cls, region):
        instances = []

        c = boto3.client(cls.service, region_name=region, aws_access_key_id=settings['zcloud_id'], aws_secret_access_key=settings['zcloud_secret'])
        r = c.describe_instances()

        if r.get('Reservations'):
            instances.extend(r['Reservations'][0]['Instances'])

        return instances



if __name__ == '__main__':
    instances = list()

    for region in ZCLOUD_REGION_LIST:
        r = Zcloud.get_instances(region)
        instances.extend(r)

    from pprint import pprint
    pprint(instances)
