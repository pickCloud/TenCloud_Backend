__author__ = 'Jon'

import hashlib

from service.base import BaseService
from tornado.gen import coroutine
from constant import INVITE_URL, DEFAULT_ENTRY_SETTING


class CompanyEntrySettingService(BaseService):
    table  = 'company_entry_setting'
    fields = 'id, cid, setting, code'

    @staticmethod
    def create_code(cid, setting=DEFAULT_ENTRY_SETTING):
        return hashlib.sha1((str(cid) + setting).encode('utf-8')).hexdigest()[:7]

    @staticmethod
    def produce_url(code):
        return INVITE_URL + code

    @coroutine
    def save_setting(self, params):
        ''' 设置员工加入条件
        :param params: {'cid', 'setting'}
        :return: INVITE_URL
        '''
        cid, setting = params['cid'], params['setting']

        code = self.create_code(str(cid), setting)

        data = yield self.select({'cid': cid}, one=True)

        if data and data['code'] != code:
            yield self.update(sets={'code': code, 'setting': setting}, conds={'cid': cid})
        else:
            arg = {
                'cid': cid,
                'setting': setting,
                'code': code
            }
            yield self.add(params=arg)
        return self.produce_url(code)

    @coroutine
    def get_setting(self, cid):
        ''' 获取员工加入条件
        :param cid: 公司id
        :return: {'setting': 'mobile,name'}
        '''
        data = yield self.select(fields='setting', conds={'cid': cid}, one=True)

        return data

    @coroutine
    def filter_by_setting(self, data, cid):
        '''
        根据公司设置过滤员工列表信息
        :param data: 员工列表信息
        :param cid: 公司id
        :return: 过滤后的员工列表信息
        '''
        display_flag = True
        company_setting = yield self.get_setting(cid)
        if 'id_card' not in company_setting['setting']:
            display_flag = False
            for i in data:
                i.pop('id_card', None)

        return display_flag, data
