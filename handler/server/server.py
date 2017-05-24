__author__ = 'Jon'

import traceback
import uuid

from tornado.websocket import WebSocketHandler
from tornado.gen import coroutine, Task
from tornado.ioloop import PeriodicCallback, IOLoop
from handler.base import BaseHandler
from constant import SERVER_TOKEN, TOKEN_FLAG


class ServerNewHandler(WebSocketHandler, BaseHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        pass

    def on_message(self, message):
        self.msg = message
        self.uuid = uuid.uuid4().hex
        self.write_message(self.uuid)

        IOLoop.current().spawn_callback(callback=self.handle_message)

        self.period = PeriodicCallback(self.check, 3000) # 设置定时函数, 3秒
        self.period.start()

    @coroutine
    def handle_message(self):
        yield Task(self.redis.hset, SERVER_TOKEN, self.uuid, 0)

    @coroutine
    def check(self):
        ''' 检查主机是否上报信息 '''
        result = yield Task(self.redis.hget, SERVER_TOKEN, self.uuid)

        if result == TOKEN_FLAG:
            self.write_message('success')
            self.period.stop()
            self.close()

    def on_close(self):
        pass


class ServerReport(BaseHandler):
    @coroutine
    def post(self):
        try:
            is_old_token = yield self.server_service.check_token(self.params['token'])

            yield self.server_service.save_report(self.params)

            if not is_old_token:
                yield self.server_service.to_feedback(self.params['token'])

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())
