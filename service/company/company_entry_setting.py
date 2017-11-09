__author__ = 'Jon'

import hashlib

from service.base import BaseService
from tornado.gen import coroutine
from constant import INVITE_URL


class CompanyEntrySettingService(BaseService):
    table  = 'company_entry_setting'
    fields = 'id, cid, setting, code'

    @coroutine
    def save_setting(self, params):
        ''' 设置员工加入条件
        :param params: {'cid', 'setting'}
        :return: INVITE_URL
        '''
        cid, setting = params['cid'], params['setting']

        code = hashlib.sha1((str(cid) + setting).encode('utf-8')).hexdigest()[:7]

        data = yield self.select(conds=['cid=%s'], params=[cid], one=True)

        if data and data['code'] != code:
            yield self.update(sets=['code=%s', 'setting=%s'], conds=['cid=%s'], params=[code, setting, cid])
        else:
            params['code'] = code
            yield self.add(params=params)

        return INVITE_URL + code

    @coroutine
    def get_setting(self, cid):
        ''' 获取员工加入条件
        :param cid: 公司id
        :return: {'setting': 'mobile,name'}
        '''
        data = yield self.select(fields='setting', conds=['cid=%s'], params=[cid], one=True)

        return data