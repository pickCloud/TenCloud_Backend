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


import json
import tornado.web
from tornado.gen import coroutine, Task

from service.cluster.cluster import ClusterService
from service.imagehub.imagehub import ImagehubService
from service.server.server import ServerService
from service.project.project import ProjectService
from service.project.project_versions import ProjectVersionService
from service.repository.repository import RepositoryService
from service.user.user import UserService
from service.user.sms import SMSService
from service.file.file import FileService
from service.server.server_operation import ServerOperationService

from constant import SESSION_TIMEOUT, SESSION_KEY
from utils.general import json_dumps, json_loads
from setting import settings


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


    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    @property
    def log(self):
        return self.application.log

    @coroutine
    def prepare(self):
        ''' 获取用户信息 && 获取请求的参数, json类型

            Usage:
                >>> self.current_user['id']
                >>> self.params['x']
        '''
        user_id = self.get_secure_cookie('user_id')

        if user_id:
            self.current_user = yield self.get_session(user_id.decode('utf-8'))

        self.params = {}

        if self.request.headers.get("Content-Type", "").startswith("application/json") and self.request.body != "":
            self.params = json.loads(self.request.body.decode('utf-8'))

    def guarantee(self, *args):
        ''' 接口参数是否完整
        '''
        for arg in args:
            try:
                self.params[arg]
            except KeyError:
                raise AttributeError('缺少参数 %s' % arg)

    def strip(self, *args):
        ''' 对self.params的一些参数进行strip
        '''
        for arg in args:
            self.params[arg].strip()

    def success(self, data=None, message="success"):
        ''' 响应成功, 返回数据
        '''
        self.write({"status": 0, "message": message, "data": data})

    def error(self, message='系统繁忙, 请重新尝试', data=None, code=400):
        ''' 响应失败, 返回错误原因
        '''
        self.set_status(code, message)
        self.write({"status": 1, "message": message, "data": data})

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