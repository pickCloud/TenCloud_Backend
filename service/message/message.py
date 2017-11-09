__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService


class MessageService(BaseService):
    table  = 'message'
    fields = 'id, owner, content, mode'

    @coroutine
    def fetch(self, params):
        ''' 获取个人消息
        :param params: {'owner', 'mode'} # mode可选
        :return:
        '''
        c, p = self.make_pair(params)

        data = yield self.select(conds=c, params=p)

        return data

    @coroutine
    def check_owner(self, params):
        ''' 检验消息所有者
        :param params: {'owner', 'id'}
        '''
        c, p = self.make_pair(params)

        data = yield self.select(conds=c, params=p)

        if not data:
            raise ValueError('非消息所有者')