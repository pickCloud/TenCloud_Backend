__author__ = 'Jon'

import traceback
import uuid

from tornado.websocket import WebSocketHandler
from tornado.gen import coroutine, Task
from tornado.ioloop import PeriodicCallback
from handler.base import BaseHandler
from utils.db import REDIS
from constant import SERVER_TOKEN


class ServerNewHandler(WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        pass

    def on_message(self, message):
        ''' 设置定时函数 '''
        self.uuid = uuid.uuid4().hex
        self.write_message(self.uuid)
        self.period = PeriodicCallback(self.check, 3000) # 3秒
        self.period.start()

    @coroutine
    def check(self):
        ''' 检查主机是否上报信息 '''
        result = yield Task(REDIS.hget, SERVER_TOKEN, self.uuid)

        if result:
            self.write_message('success')
            self.period.stop()
            self.close()

    def on_close(self):
        pass


class ServerReport(BaseHandler):
    @coroutine
    def post(self):
        try:
            yield self.server_service.save_report(self.params)

            yield self.server_service.to_feedback(self.params['token'])
            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())
