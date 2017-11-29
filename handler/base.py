__author__ = 'Jon'

'''
所有handler处理的父类

说明
---------------
* 所有service的初始化
* 复写tornado.web.RequestHandler的一些常用方法
* 子类使用的共同函数抽象
* api需要发送json, 存储在self.params
* handler都需要try...catch
    try:
    except:
        self.error()
        self.log.error(traceback.format_exc())
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
from service.imagehub.imagehub import ImagehubService
from service.message.message import MessageService
from service.permission.permission import PermissionService
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
    imagehub_service = ImagehubService()
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
    def prepare(self):
        ''' 获取用户信息 && 获取请求的参数, json类型

            Usage:
                >>> self.current_user['id']
                >>> self.params['x']
        '''
        token = self.request.headers['Authorization'].split(' ')[1] if self.request.headers.get('Authorization') else ''

        if token:
            user_id = self.decode_auth_token(token)

            if user_id:
                self.current_user = yield self.get_session(user_id)

        self.params = {}

        if self.request.headers.get('Content-Type', '').startswith('application/json') and self.request.body != '':
            self.params = json.loads(self.request.body.decode('utf-8'))

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