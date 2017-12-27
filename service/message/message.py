__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import MSG_PAGE_NUM, MSG_STATUS, MSG_MODE, MSG_SUB_MODE, MSG
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

        data = yield self.select(params, extra=extra)

        unread = [d['id'] for d in data if d['status'] == MSG_STATUS['unread']]
        if unread:
            yield self.set_read(unread)

        return data

    @coroutine
    def set_read(self, ids):
        ''' 把未读消息设置已读
        :param ids: [1, 2]
        '''
        if ids:
            yield self.update(sets={'status': MSG_STATUS['read']}, conds={'id': ids})

    @coroutine
    def check_owner(self, params):
        ''' 检验消息所有者
        :param params: {'owner', 'id'}
        '''
        data = yield self.select(params)

        if not data:
            raise ValueError('非消息所有者')

    @coroutine
    def notify_change(self, params):
        '''
        企业信息变更后发送消息通知员工
        :param params:
        :return:
        '''
        for owner in params['owners']:
            yield self.add({
                'owner': owner,
                'content': MSG['change'].format(company_name=params['company_name'], admin_name=params['admin_name']),
                'mode': MSG_MODE['change'],
                'sub_mode': MSG_SUB_MODE['change'],
                'tip': '{}:'.format(params['cid'])
            })

    @coroutine
    def notify_verify(self, params):
        '''
        通知用户申请已通过或被拒绝
        :param params:
        :return:
        '''
        yield self.add({
            'owner': params['owner'],
            'content': MSG['application'][params['mode']].format(company_name=params['company_name'], admin_name=params['admin_name']),
            'mode': MSG_MODE['application'],
            'sub_mode': MSG_SUB_MODE[params['mode']],
            'tip': params['tip']
        })
