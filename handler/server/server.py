__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler


class ServerHander(BaseHandler):
    @coroutine
    def get(self, *args, **kwargs):
        try:
            count = yield self.server_service.get_status()
            self.write(str(count))
        except:
            self.log.error(traceback.format_exc())