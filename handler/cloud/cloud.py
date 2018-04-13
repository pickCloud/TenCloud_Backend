import random
from tornado.gen import coroutine

from utils.decorator import is_login
from utils.context import catch
from utils.general import json_dumps
from utils.error import AppError
from utils.security import Aes
from handler.base import BaseHandler
from constant import TENCLOUD_PROVIDER_LIST, TENCLOUD_PROVIDER_NAME

class CloudsHandler(BaseHandler):
    @coroutine
    def get(self):
        """
        @api {get} /api/clouds/support 支持的公有云列表
        @apiName CloudsHandler
        @apiGroup Cloud
        @apiSuccessExample {json} Success-Response:
        HTTP/1.1 200 OK
        {
            "status": 0,
            "msg": "success",
            "data": [
                {
                    "name": string,
                    "id": int, 厂商的内部id
                }
                ...
            ]
        }
        """
        with catch(self):
            data = [{'name': k, 'id': v} for k, v in TENCLOUD_PROVIDER_LIST.items()]
            self.success(data)


class CloudCredentialHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/cloud/credential 公有云厂商认证
        @apiName CloudCredentialHandler
        @apiGroup Cloud

        @apiParam {Number} cloud_type 厂商内部id
        @apiParam {Object} content 凭证内容

        @apiSuccessExample {json} Success-Response:
        HTTP/1.1 200 OK
        {
            "status": 0,
            "msg": "success",
            "data": [
                {
                    "is_add": int 0:未添加 1:已经添加,
                    "instance_id": string,
                    "public_ip": string,
                    "inner_ip": string,
                    "net_type": string,
                    "region_id": string
                }
            ]
        }
        """
        with catch(self):
            self.params.update(self.get_lord())
            provider = TENCLOUD_PROVIDER_NAME[self.params['cloud_type']]

            data = yield self.server_service.search_fc_instance({'provider': provider})

            self.success(data)

    @is_login
    @coroutine
    def put(self):
        """
        @api {put} /api/cloud/credential 公有云机器添加
        @apiName CloudCredentialHandler
        @apiGroup Cloud

        @apiParam {Number} cloud_type 厂商内部id
        @apiParam {String} provider
        @apiParam {String} public_ip
        @apiParam {String} instance_id

        @apiUse Success
        """
        with catch(self):
            self.params.update(self.get_lord())

            for data in self.params['data']:
                yield self.server_service.add({
                    'name': '%s演示%s'.format(data['provider'], random.randint(1, 100)),
                    'public_ip': data['public_ip'],
                    'cluster_id': data['cloud_type'],
                    'instance_id': data['instance_id'],
                    'lord': self.params['lord'],
                    'form': self.params['form']
                })

            self.success()

    # 仅供测试用，方面前端删除测试账号
    @is_login
    @coroutine
    def delete(self):
        """
        @api {delete} /api/cloud/credential 公有云厂商认证
        @apiName CloudCredentialHandler
        @apiGroup Cloud


        @apiUse Success
        """
        with catch(self):
            params = self.get_lord()
            conds = {
                'lord': params['lord'],
                'form': params['form']
            }
            yield self.cloud_credentials_service.delete(conds=conds)
