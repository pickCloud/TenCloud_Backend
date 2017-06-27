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

import json
import tornado.web

from tornado.gen import coroutine
from service.cluster.cluster import ClusterService
from service.imagehub.imagehub import ImagehubService
from service.server.server import ServerService
from service.project.project import ProjectService
from service.repository.repository import RepositoryService


class BaseHandler(tornado.web.RequestHandler):
    cluster_service = ClusterService()
    imagehub_service = ImagehubService()
    server_service  = ServerService()
    project_service = ProjectService()
    repos_service = RepositoryService()

    @property
    def db(self):
        return self.application.db

    @property
    def redis(self):
        return self.application.redis

    @property
    def log(self):
        return self.application.log

    def prepare(self):
        ''' 获取请求的参数, json类型

            Usage:
                >>> self.params['x']
        '''
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
                raise AttributeError('缺少 %s' % arg)

    def success(self, data=None, message="success"):
        ''' 响应成功, 返回数据
        '''
        self.write({"status": 0, "message": message, "data": data})

    def error(self, message='系统繁忙, 请重新尝试', data=None, code=400):
        ''' 响应失败, 返回错误原因
        '''
        self.set_status(code, message)
        self.write({"status": 1, "message": message, "data": data})
