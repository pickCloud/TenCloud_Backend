
from tornado.gen import coroutine

from service.base import BaseService
from constant import TENCLOUD_PROVIDER_LIST, ERR_TIP, ALIYUN_DOMAIN, QCLOUD_DOMAIN
from utils.error import AppError
from service.cloud.aliyunecs import AliyunECSBase
from service.cloud.qcloudcvm import QcloudCVMBase
from service.cloud.zcloudec2 import ZcloudEC2


class CloudCredentialsService(BaseService):
    table = 'cloud_credentials'
    fields = 'id', 'content', 'cloud_type', 'lord', 'form'

    @coroutine
    def check_instance(self, instance_id):
        sql = """
            SELECT instance_id FROM instance where instance_id=%s LIMIT 1
            """
        cur = yield self.db.execute(sql, [instance_id])
        if len(cur.fetchall()):
            return True
        return False

    @coroutine
    def get_server_info(self, params):
        """
        :param params: {'cloud_type': int, 'content': str}
        :return:
        """
        try:
            cloud_type = params['cloud_type']
            credentials = params['content']
        except:
            raise AppError(ERR_TIP['arg_error']['msg'], ERR_TIP['arg_error']['sts'])

        if cloud_type not in TENCLOUD_PROVIDER_LIST.values():
            raise AppError(ERR_TIP['cloud_unsupported']['msg'], ERR_TIP['cloud_unsupported']['sts'])

        resp = []
        if cloud_type == TENCLOUD_PROVIDER_LIST['aliyun']:
            access_key = credentials['access_key']
            access_secret = credentials['access_secret']
            ecs = AliyunECSBase(access_key_id=access_key, access_key_secret=access_secret, ecs_domain=ALIYUN_DOMAIN)
            for i in ecs.get_all_region_instance():
                is_add = yield self.check_instance(i['InstanceId'])
                ret = {
                    'is_add': is_add,
                    'instance_id': i['InstanceId'],
                    'public_ip': ','.join(i['PublicIpAddress']['IpAddress']) if len(i['PublicIpAddress']['IpAddress']) else '',
                    'inner_ip': ','.join(i['InnerIpAddress']['IpAddress']) if len(i['InnerIpAddress']['IpAddress']) else '',
                    'net_type': i.get('InstanceNetworkType', ''),
                    'region_id': i.get('RegionId')
                }
                resp.append(ret)
        elif cloud_type == TENCLOUD_PROVIDER_LIST['qcloud']:
            access_key = credentials['access_key']
            access_secret = credentials['access_secret']
            cvm = QcloudCVMBase(access_key_id=access_key, access_key_secret=access_secret, cvm_domain=QCLOUD_DOMAIN)
            for i in cvm.get_all_region_instance():
                is_add = yield self.check_instance(i['InstanceId'])
                ret = {
                    'is_add': is_add,
                    'instance_id': i['InstanceId'],
                    'public_ip': ','.join(i.get('PublicIpAddresses')) if len(i.get('PublicIpAddresses')) else '',
                    'inner_ip': ','.join(i.get('PrivateIpAddresses')) if len(i.get('PrivateIpAddresses')) else '',
                    'net_type': 'vpc',
                    'region_id': i.get('region_id')
                }
                resp.append(ret)
        elif cloud_type == TENCLOUD_PROVIDER_LIST['zcloud']:
            access_key = credentials['access_key']
            access_secret = credentials['access_secret']
            ec2 = ZcloudEC2(access_key_id=access_key, access_key_secret=access_secret)
            for i in ec2.get_all_region_instance():
                is_add = yield self.check_instance(i['InstanceId'])
                ret = {
                    'is_add': is_add,
                    'instance_id': i['InstanceId'],
                    'public_ip': i.get('PublicIpAddress', ''),
                    'inner_ip': i.get('PrivateIpAddress', ''),
                    'net_type': 'vpc',
                    'region_id': i.get('region_id')
                }
                resp.append(ret)
        return resp