
from tornado.gen import coroutine

from utils.decorator import is_login
from utils.context import catch
from utils.general import json_dumps
from utils.error import AppError
from utils.security import Aes
from handler.base import BaseHandler
from constant import TENCLOUD_PROVIDER_LIST, ERR_TIP

class ServerCloudsHandler(BaseHandler):
    @coroutine
    def get(self):
        """
        @api {get} /api/clouds/support 支持的公有云列表
        @apiName ServerCloudsHandler
        @apiGroup Server
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


class ServerCloudCredentialHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/cloud/credential 公有云厂商认证
        @apiName ServerCloudCredentialHandler
        @apiGroup Server

        @apiParam cloud_type 厂商内部id
        @apiParam content 凭证内容

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
            arg = {
                'cloud_type': self.params['cloud_type'],
                'content': Aes.encrypt(str(self.params['content'])),
                'lord': self.params['lord'],
                'form': self.params['form']
            }
            key_id = yield self.cloud_credentials_service.select(fields='id', conds={'content':arg['content']}, one=True)
            if key_id is not None:
                raise AppError(ERR_TIP['cloud_access_key_exist']['msg'], ERR_TIP['cloud_access_key_exist']['sts'])

            data = yield self.cloud_credentials_service.get_server_info(self.params)
            yield self.cloud_credentials_service.add(arg)
            self.success(data)
