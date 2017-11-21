__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import MSG_PAGE_NUM, MSG_STATUS
from utils.general import get_in_formats


class MessageService(BaseService):
    table  = 'message'
    fields = 'id, owner, content, mode, sub_mode, tip, status'

    @coroutine
    def fetch(self, params):
        ''' 获取个人消息
        :param params: {'owner', 'status', 'page'} # status, page可选
        :return:
        '''
        page = params.pop('page', None)

        extra = ' ORDER BY update_time DESC '

        if page:
            extra += 'LIMIT {},{}'.format((page - 1) * MSG_PAGE_NUM, MSG_PAGE_NUM)

        c, p = self.make_pair(params)

        data = yield self.select(conds=c, params=p, extra=extra)

        unread = [d['id'] for d in data if d['status']==0]
        if unread:
            yield self.set_read(unread)

        return data

    @coroutine
    def set_read(self, ids):
        ''' 把未读消息设置已读
        :param ids: [1, 2]
        '''
        if ids:
            yield self.update(sets=['status=%s'], conds=[get_in_formats('id', ids)], params=[MSG_STATUS['read']] + ids)

    @coroutine
    def check_owner(self, params):
        ''' 检验消息所有者
        :param params: {'owner', 'id'}
        '''
        c, p = self.make_pair(params)

        data = yield self.select(conds=c, params=p)

        if not data:
            raise ValueError('非消息所有者')