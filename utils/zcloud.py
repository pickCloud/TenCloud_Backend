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

    @classmethod
    def describe_image(cls, data):
        c = cls._get_client(data['region_id'])
        images = c.describe_images(ImageIds=[data['ImageId']])
        resp = list()
        if not len(images['Images']):
            return resp

        for one in images['Images']:
            image = dict()
            image['ImageId'] = one.get('ImageId','')
            image['ImageVersion'] = ''
            image['OSType'] = one.get('ImageType','')
            image['Platform'] = one.get('Platform','')
            image['Architecture'] = one.get('Architecture','')
            image['ImageName'] = one.get('Name','')
            image['Size'] = ''
            image['OSName'] = ''
            resp.append(image)
        return resp

    @classmethod
    def describe_disk(cls, data):
        c = cls._get_client(data['region_id'])
        disks = c.describe_volumes()
        resp = list()
        if not len(disks['Volumes']):
            return resp
        for one in disks['Volumes']:
            disk = dict()
            disk['DiskId'] = one.get('VolumeId','')
            disk['DiskName'] = ''
            disk['Type'] = ''
            disk['Category'] = one.get('VolumeType','')
            disk['Size'] = one['Size']
            disk['InstanceId'] = one.get('Attachments', [])[0].get('InstanceId','')
            disk['Device'] = one.get('Attachments', [])[0].get('Device','')
            resp.append(disk)
        return resp


if __name__ == '__main__':
    # image_1 = Zcloud.describe_image({'region_id': 'ap-southeast-1', 'ImageId': ['ami-68097514']})
    # print(image_1)
    # image_2 = Zcloud.describe_image({'region_id': 'us-west-2', 'ImageId':['ami-b5c509cd']})
    # print(image_2)
    disks_1 = Zcloud.describe_disk({'region_id': 'us-west-2'})
    print(disks_1)
    # instances = list()
    #
    # for region in ZCLOUD_REGION_LIST:
    #    r = Zcloud.get_instances(region)
    #    instances.extend(r)

    # r = Zcloud.get_instances(region='us-west-2', InstanceIds=['i-079a7ab649fb51f7d'])
    # instances.extend(r)

    # from pprint import pprint
    # pprint(instances)