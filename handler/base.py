__author__ = 'Jon'

'''
所有handler处理的父类

说明
---------------
* 所有service的初始化
* 复写tornado.web.RequestHandler的一些常用方法
* 子类使用的共同函数抽象
'''

import json
import tornado.web

from tornado.gen import coroutine
from service.cluster.cluster import ClusterService


class BaseHandler(tornado.web.RequestHandler):
    cluster_service = ClusterService()

    @property
    def db(self):
        return self.application.db

    @property
    def log(self):
        return self.application.log

    @coroutine
    def prepare(self):
        '''获取请求的参数, json类型
           Usage:
               >>> self.params['x']
        '''
        self.params = {}

        if self.request.headers.get("Content-Type", "").startswith("application/json") and self.request.body != "":
            self.params = json.loads(self.request.body.decode('utf-8'))

    def success(self, data=None, message="success"):
        """响应成功, 返回数据"""
        self.write({"status": 0, "message": message, "data": data})

    def error(self, message='系统繁忙, 请重新尝试', data=None, code=400):
        """响应失败, 返回错误原因"""
        self.set_status(code, message)
        self.write({"status": 1, "message": message, "data": data})
