__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService


class ServerService(BaseService):
    @coroutine
    def get_status(self):
        count = yield self.db.execute('select count(*) from for_test')
        data = count.fetchone()

        return data[0]
