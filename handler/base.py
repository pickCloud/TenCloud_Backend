__author__ = 'Jon'

'''
所有handler处理的父类

说明
---------------
* 所有service的初始化
* 复写tornado.web.RequestHandler的一些常用方法
* handler子类使用的共同函数抽象
* api发送的参数, 存储在self.params
* handler都需要catch exception
    from util.context import catch

    with catch(self):
        self.success()
'''

#################################################################################
# Handler共用的apiDefine
#################################################################################
"""
@apiDefine Success
@apiSuccessExample {json} Success-Response:
    HTTP/1.1 200 OK
    {
        "status": 0,
        "message": "success",
        "data": {}
    }
"""


""""
@apiDefine apiHeader
@apiHeaderExample {json} Header-Example:
     {
       "cid": 1
     }
"""

import jwt
import json
import datetime
import traceback

import tornado.web
from service.permission.permission_template import PermissionTemplateService
from tornado.gen import coroutine, Task
from tornado.websocket import WebSocketHandler

from constant import SESSION_TIMEOUT, SESSION_KEY, TOKEN_EXPIRES_DAYS
from service.cluster.cluster import ClusterService
from service.company.company import CompanyService
from service.company.company_application import CompanyApplicationService
from service.company.company_employee import CompanyEmployeeService
from service.company.company_entry_setting import CompanyEntrySettingService
from service.file.file import FileService
from service.message.message import MessageService
from service.permission.permission import PermissionService, UserPermissionService
from service.project.project import ProjectService
from service.project.project_versions import ProjectVersionService
from service.repository.repository import RepositoryService
from service.server.server import ServerService
from service.server.server_operation import ServerOperationService
from service.user.sms import SMSService
from service.user.user import UserService
from setting import settings
from utils.general import json_dumps, json_loads


class BaseHandler(tornado.web.RequestHandler):
    cluster_service = ClusterService()
    server_service = ServerService()
    project_service = ProjectService()
    repos_service = RepositoryService()
    project_versions_service = ProjectVersionService()
    user_service = UserService()
    file_service = FileService(ak=settings['qiniu_access_key'], sk=settings['qiniu_secret_key'])
    sms_service = SMSService()
    server_operation_service = ServerOperationService()
    company_service = CompanyService()
    company_employee_service = CompanyEmployeeService()
    company_entry_setting_service = CompanyEntrySettingService()
    company_application_service = CompanyApplicationService()
    message_service = MessageService()
    permission_template_service = PermissionTemplateService()
    permission_service = PermissionService()
    user_permission_service = UserPermissionService()


    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    @property
    def log(self):
        return self.application.log

    def encode_auth_token(self, user_id):
        ''' 创建token，包含用户id
        '''
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=TOKEN_EXPIRES_DAYS),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            token = jwt.encode(payload, settings['token_secret'], algorithm='HS256')

            return token.decode('UTF-8')
        except Exception as e:
            self.log.error(traceback.format_exc())
            return e

    def decode_auth_token(self, auth_token):
        ''' 解析token，提取用户id
        '''
        try:
            payload = jwt.decode(auth_token, settings['token_secret'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            self.log.error('Signature expired: {}'.format(auth_token))
            return ''
        except jwt.InvalidTokenError:
            self.log.error('Invalid token: {}'.format(auth_token))
            return ''



    @coroutine
    def _with_token(self):
        token = self.request.headers.get('Authorization')

        if token:
            user_id = self.decode_auth_token(token)

            if user_id:
                self.current_user = yield self.get_session(user_id)

    def _decode_params(self):
        ''' 对self.params的values进行decode, 而且如果value长度为1, 返回最后一个元素
        '''
        for k, v in self.params.items():
            if len(v) == 1:
                self.params[k] = v[-1].decode('utf-8')
            else:
                self.params[k] = [e.decode('utf-8') for e in v]

    @coroutine
    def prepare(self):
        ''' 获取用户信息 && 获取请求的参数, json类型

            Usage:
                >>> self.current_user['id']
                >>> self.params['x']
        '''
        yield self._with_token()

        self.params = {}

        if self.request.headers.get('Content-Type', '').startswith('application/json') and self.request.body != '':
            self.params = json.loads(self.request.body.decode('utf-8'))
        else:
            self.params = self.request.arguments.copy()
            self._decode_params()

        if self.request.headers.get('Cid'):
            self.params['cid'] = int(self.request.headers['Cid'])


    def on_finish(self):
        self.log.debug('{status} {method} {uri} {payload}'.format(status=self._status_code,
                                                                  method=self.request.method,
                                                                  uri=self.request.uri,
                                                                  payload=str(self.params or '')))

    def guarantee(self, *args):
        ''' 接口参数是否完整
        '''
        for arg in args:
            if not self.params.get(arg):
                raise AttributeError('参数 %s 不能为空' % arg)

    def strip(self, *args):
        ''' 对self.params的一些参数进行strip
        '''
        for arg in args:
            self.params[arg].strip()

    def success(self, data=None, message='成功'):
        ''' 响应成功, 返回数据
        '''
        self.write({"status": 0, "message": message, "data": data})

    def error(self, message='', data=None, code=400, status=1):
        ''' 响应失败, 返回错误原因
        '''
        self.set_status(code)
        self.write({"status": status, "message": message, "data": data})

    @coroutine
    def set_session(self, user_id, data):
        ''' 添加/更新 Session
        :param user_id: user表id
        :param data:    dict，key对应user表的字段
        '''
        yield Task(self.redis.setex, SESSION_KEY.format(user_id=user_id), SESSION_TIMEOUT, json_dumps(data))

    @coroutine
    def get_session(self, user_id):
        ''' 获取 Session
        '''
        data = yield Task(self.redis.get, SESSION_KEY.format(user_id=user_id))

        return json_loads(data)

    @coroutine
    def del_session(self, user_id):
        ''' 删除 Session
        '''
        yield Task(self.redis.delete, SESSION_KEY.format(user_id=user_id))


class WebSocketBaseHandler(WebSocketHandler, BaseHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self.write_message('open')

    def on_message(self, message):
        pass

    def on_close(self):
        pass