__author__ = 'Jon'


import boto3
from constant import ZCLOUD_REGION_LIST

from setting import settings


class Zcloud:
    service = 'ec2'

    @classmethod
    def _get_client(cls, region):
        session = boto3.session.Session()

        return session.client(cls.service, region_name=region, aws_access_key_id=settings['zcloud_id'], aws_secret_access_key=settings['zcloud_secret'])

    @classmethod
    def get_instances(cls, region, **kwargs):
        instances = []

        c = cls._get_client(region)


        r = c.describe_instances(**kwargs) if kwargs else c.describe_instances()

        if r.get('Reservations'):
            instances.extend(r['Reservations'][0]['Instances'])

        return instances

    @classmethod
    def stop(cls, data):
        c = cls._get_client(data['region_id'])

        c.stop_instances(InstanceIds=[data['instance_id']])

    @classmethod
    def start(cls, data):
        c = cls._get_client(data['region_id'])

        c.start_instances(InstanceIds=[data['instance_id']])

    @classmethod
    def reboot(cls, data):
        c = cls._get_client(data['region_id'])

        c.reboot_instances(InstanceIds=[data['instance_id']])

    @classmethod
    def get_public_ip(cls, data):
        r = cls.get_instances(region=data['region_id'], InstanceIds=[data['instance_id']])

        return r[0].get('PublicIpAddress', '')

if __name__ == '__main__':
    instances = list()

    for region in ZCLOUD_REGION_LIST:
       r = Zcloud.get_instances(region)
       instances.extend(r)

    # r = Zcloud.get_instances(region='us-west-2', InstanceIds=['i-079a7ab649fb51f7d'])
    # instances.extend(r)

    from pprint import pprint
    pprint(instances)