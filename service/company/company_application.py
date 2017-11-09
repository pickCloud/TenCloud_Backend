__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService


class CompanyApplicationService(BaseService):
    table  = 'company_application'
    fields = 'id, cid, uid, mobile, name, id_card, status'

    @coroutine
    def get(self, code):
        '''
        :param code: 申请链接的code
        :return: {'company_name', 'contact', 'setting'}
        '''
        sql = '''
            SELECT c.id AS cid, c.name AS company_name, c.contact, ce.setting
            FROM company c
            JOIN company_entry_setting ce ON c.id = ce.cid
            WHERE ce.code = %s
        '''

        cur = yield self.db.execute(sql, code)

        data = cur.fetchone()

        return data
