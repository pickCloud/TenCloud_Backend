__author__ = 'Jon'


import boto3
from constant import ZCLOUD_REGION_LIST


class ZcloudEC2:
    service = 'ec2'

    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    def _get_client(self, region):
        session = boto3.session.Session()
        client = session.client(
            service_name=self.service,
            region_name=region,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.access_key_secret
        )
        return client

    def get_all_region_instance(self):
        all_region_instances = list()
        for region in ZCLOUD_REGION_LIST:
            client = self._get_client(region)
            r = client.describe_instances()
            if r.get('Reservations'):
                for one in r['Reservations'][0]['Instances']:
                    one.update({'region_id': region})
                    all_region_instances.append(one)
        return all_region_instances

