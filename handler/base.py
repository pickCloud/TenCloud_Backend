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

from service.server.server import ServerService


class BaseHandler(tornado.web.RequestHandler):
    server_service = ServerService()

    @property
    def db(self):
        return self.application.db

    @property
    def log(self):
        return self.application.log

    def init_params(self):
        '''获取请求的参数
           Usage::
               >>> self.init_params()
               >>> self.params['xxx']
        '''
        self.params = {}

        if self.request.method == 'GET':
            self.params = self.request.query_arguments
        elif self.request.method in ('POST', 'PUT'):
            self.params = self.request.body_arguments

        for k, v in self.params.items():
            self.params[k] = v if len(v) > 1 else v[0]

    def write_json(self, data):
        self.write(json.dumps(data))