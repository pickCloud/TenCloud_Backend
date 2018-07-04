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
@apiDefine cidHeader
@apiHeaderExample {json} Header-Example:
     {
       "cid": 1
     }
"""

import jwt
import time
import datetime
import traceback
import os

import tornado.web
from service.permission.permission_template import PermissionTemplateService
from tornado.gen import coroutine
from tornado.websocket import WebSocketHandler

from constant import SESSION_TIMEOUT, SESSION_KEY, TOKEN_EXPIRES_DAYS, RIGHT, SERVICE, SUCCESS_STATUS, FAILURE_STATUS, \
                     FORM_COMPANY, FORM_PERSON, USER_LATEST_TOKEN, FAILURE_CODE, K8S_APPLY_CMD, K8S_DELETE_CMD
from service.cluster.cluster import ClusterService
from service.company.company import CompanyService
from service.company.company_employee import CompanyEmployeeService
from service.company.company_entry_setting import CompanyEntrySettingService
from service.file.file import FileService
from service.message.message import MessageService
from service.permission.permission import PermissionService, UserPermissionService, UserAccessServerService, \
                                          UserAccessProjectService, UserAccessFilehubService, UserAccessApplicationService
from service.application.application import ApplicationService
from service.application.deployment import DeploymentService, ReplicaSetService, PodService
from service.application.service import ServiceService, EndpointService
from service.imagehub.image import ImageService
from service.project.project import ProjectService
from service.project.project_versions import ProjectVersionService
from service.repository.repository import RepositoryService
from service.server.server import ServerService
from service.server.server_operation import ServerOperationService
from service.user.sms import SMSService
from service.user.user import UserService
from service.label.label import LabelService
from service.cloud.cloud_credentials import CloudCredentialsService
from setting import settings
from utils.general import json_dumps, json_loads
from utils.datetool import seconds_to_human
from utils.error import AppError
from utils.context import catch
from utils.ssh import SSH

class BaseHandler(tornado.web.RequestHandler):
    cluster_service = ClusterService()
    server_service = ServerService()
    project_service = ProjectService()
    application_service = ApplicationService()
    image_service = ImageService()
    deployment_service = DeploymentService()
    replicaset_service = ReplicaSetService()
    pod_service = PodService()
    service_service = ServiceService()
    endpoint_service = EndpointService()
    repos_service = RepositoryService()
    project_versions_service = ProjectVersionService()
    user_service = UserService()
    file_service = FileService(ak=settings['qiniu_access_key'], sk=settings['qiniu_secret_key'])
    sms_service = SMSService()
    label_service = LabelService()
    server_operation_service = ServerOperationService()
    company_service = CompanyService()
    company_employee_service = CompanyEmployeeService()
    company_entry_setting_service = CompanyEntrySettingService()
    message_service = MessageService()
    permission_template_service = PermissionTemplateService()
    permission_service = PermissionService()
    user_permission_service = UserPermissionService()
    user_access_server_service = UserAccessServerService()
    user_access_project_service = UserAccessProjectService()
    user_access_filehub_service = UserAccessFilehubService()
    cloud_credentials_service = CloudCredentialsService()
    user_access_application_service = UserAccessApplicationService()


    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    @property
    def log(self):
        return self.application.log

    def is_latest_token(self):
        ''' 判断token是否最新
        '''
        data = json_loads(self.redis.hget(USER_LATEST_TOKEN, str(self.current_user['id'])))

        flag = True if data and data.get('token', '') == self.params['token'] else False

        return flag, data

    def encode_auth_token(self, user_id):
        ''' 创建token，包含用户id
        '''
        try:
            t = datetime.datetime.now() + datetime.timedelta(days=TOKEN_EXPIRES_DAYS)
            exp = datetime.datetime(t.year, t.month, t.day, 3, 0) # 凌晨3点，防止用户在使用中出现token过期

            payload = {
                'exp': exp,
                'iat': datetime.datetime.now(),
                'uid': user_id
            }
            token = jwt.encode(payload, settings['token_secret'], algorithm='HS256')

            return token.decode('UTF-8')
        except Exception as e:
            self.log.error(traceback.format_exc())
            raise ValueError(e)

    def decode_auth_token(self, auth_token):
        ''' 解析token，提取用户id
        '''
        try:
            payload = jwt.decode(auth_token, settings['token_secret'])

            if payload['exp'] < time.time():
                # raise AppError('过期token', code=403)
                pass
            return payload.get('uid') or payload.get('sub') # sub为之前的字段名，暂时保留
        except jwt.ExpiredSignatureError:
            self.log.error('Signature expired: {}'.format(auth_token))
            # raise AppError('无效签名', code=403)
        except jwt.InvalidTokenError:
            self.log.error('Invalid token: {}'.format(auth_token))
            # raise AppError('无效token', code=403)

    def _with_token(self):
        token = self.request.headers.get('Authorization', '')

        return (self.decode_auth_token(token), token) if token else ('', '')

    def _decode_params(self):
        ''' 对self.params的values进行decode, 而且如果value长度为1, 返回最后一个元素
        '''
        for k, v in self.params.items():
            if len(v) == 1:
                self.params[k] = v[-1].decode('utf-8')
            else:
                self.params[k] = [e.decode('utf-8') for e in v]

    def prepare(self):
        ''' 获取用户信息 && 获取请求的参数

            Usage:
                >>> self.current_user['id']
                >>> self.params['x']
        '''
        with catch(self):
            self.params = {}

            user_id, token = self._with_token()

            if user_id:
                self.current_user = self.get_session(user_id)

            if self.request.headers.get('Content-Type', '').startswith('application/json') and self.request.body != '':
                self.params = json_loads(self.request.body.decode('utf-8'))
            else:
                self.params = self.request.arguments.copy()
                self._decode_params()

            # 从这开始，才对self.params修改
            if self.request.headers.get('Cid'):
                self.params['cid'] = int(self.request.headers['Cid'])

            self.params['token'] = token

    def on_finish(self):
        self.params.pop('token', None)

        if self.current_user:
            self.params['session_id'] = self.current_user['id']

        self.log.debug('{status} {method} {uri} {payload}'.format(status=self._status_code,
                                                                  method=self.request.method,
                                                                  uri=self.request.uri,
                                                                  payload=self.params))

    def get_lord(self):
        ''' lord, form是数据库字段, lord(cid/uid), form(1个人, 2公司)
        '''
        return {'lord': self.params['cid'], 'form': FORM_COMPANY} if self.params.get('cid') else {'lord': self.current_user['id'], 'form': FORM_PERSON}

    def get_current_name(self):
        '''
        获取当前用户名称，如果没有设置的话返回手机号码
        :return: 用户名称或者手机号码
        '''
        return self.current_user['name'] if self.current_user['name'] != '' else self.current_user['mobile']

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
        self.write({"status": SUCCESS_STATUS, "message": message, "data": data})

    def error(self, message='', data=None, code=FAILURE_CODE, status=FAILURE_STATUS):
        ''' 响应失败, 返回错误原因
        '''
        self.set_status(code)
        self.write({"status": status, "message": message, "data": data})

    def set_session(self, user_id, data):
        ''' 添加/更新 Session
        :param user_id: user表id
        :param data:    dict，key对应user表的字段
        '''
        self.redis.setex(SESSION_KEY.format(user_id=user_id), SESSION_TIMEOUT, json_dumps(data))

    def get_session(self, user_id):
        ''' 获取 Session
        '''
        data = self.redis.get(SESSION_KEY.format(user_id=user_id))

        return json_loads(data)

    def del_session(self, user_id):
        ''' 删除 Session
        '''
        self.redis.delete(SESSION_KEY.format(user_id=user_id))

    @coroutine
    def make_session(self, mobile, set_token=False):
        '''
        :param mobile: 用户手机号
        :param set_token: 注册/登录需要设置token
        :return: {'token'}
        '''
        params = {'mobile': mobile}

        data = yield self.user_service.select(params, one=True)
        if not data:
            yield self.user_service.add(params)
            data = yield self.user_service.select(params, one=True)

        data.pop('password', None)

        # 设置session
        self.set_session(data['id'], data)

        # 设置token
        if set_token:
            token = self.encode_auth_token(data['id'])

            self.redis.hset(USER_LATEST_TOKEN, str(data['id']), json_dumps({'token': token, 'time': seconds_to_human()}))

            return {'token': token}

    @coroutine
    def filter(self, data, service=SERVICE['s'], key='id'):
        ''' 数据权限过滤
            Usage:
                from constant import SERVICE
                >>> self.filter(data, SERVICE['key'])
        '''
        # 个人不需要过滤
        if not self.params.get('cid'): return data

        # 管理员不需要过滤
        try:
            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])
        except AppError:
            data = yield getattr(self, service['company']).filter(data, self.current_user['id'], self.params.get('cid'), key=key)

        return data


class WebSocketBaseHandler(WebSocketHandler, BaseHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        user_id = self.decode_auth_token(self.params['Authorization']) if self.params.get('Authorization') else 0
        self._current_user = {'id': user_id}
        self.params['cid'] = int(self.params.get('Cid'))

        params = {'cid': self.params['cid'], 'uid': self.current_user['id'], 'pids': RIGHT['add_server']}

        try:
            self.user_permission_service.ws_check_permission(params)
        except Exception as e:
            self.write_message(str(e))
            self.close()
        else:
            self.write_message('open')

    def on_message(self, message):
        pass

    def on_close(self):
        pass

    def k8s_delete(self, params, out_func=None):
        if params.get('obj_type') and params.get('obj_name'):
            cmd = K8S_DELETE_CMD + ' '.join([params['obj_type'], params['obj_name']])
        else:
            return '', ''
        ssh = SSH(hostname=params['public_ip'], port=22, username=params['username'], passwd=params['passwd'])
        out, err = ssh.exec_rt(cmd, out_func)
        return out, err

    def k8s_apply(self, params, out_func=None):
        cmd = K8S_APPLY_CMD + params['filename']
        ssh = SSH(hostname=params['public_ip'], port=22, username=params['username'], passwd=params['passwd'])
        out, err = ssh.exec_rt(cmd, out_func)
        return out, err

    def save_yaml(self, app_name, obj_name, obj_type, yaml):
        full_path = os.path.join('/var/www/Dashboard/static', 'yaml')
        if not os.path.exists(full_path): os.makedirs(full_path)

        filename = app_name + "." + obj_name + "." + obj_type + ".yaml"
        fullname = os.path.join(full_path, filename)

        with open(fullname, 'wb') as f:
            f.write(yaml.encode())

        return filename
