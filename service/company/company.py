__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import APPLICATION_STATUS, MSG, MSG_MODE, FULL_DATE_FORMAT, MSG_SUB_MODE

class CompanyService(BaseService):
    table  = 'company'
    fields = 'id, name, contact, mobile, description, image_url'

    @coroutine
    def get_companies(self, params):

        status = 'and ce.status = %s'
        arg = [FULL_DATE_FORMAT, FULL_DATE_FORMAT, params['uid']]

        is_pass = params['is_pass']
        if is_pass == 3:
            status = 'and ( ce.status = 1 or ce.status = 2 )'
        elif is_pass == 4:
            status = ''
        else:
            arg.append(is_pass)

        sql = """

            SELECT c.id AS cid, c.name AS company_name, ce.is_admin AS is_admin, c.image_url, ces.code,
                   DATE_FORMAT(ce.create_time, %s) AS create_time, DATE_FORMAT(ce.update_time, %s) AS update_time, ce.status
            FROM company_employee ce
            JOIN company c ON ce.cid = c.id
            LEFT JOIN company_entry_setting ces ON ces.cid = ce.cid
            WHERE ce.uid = %s {status}
        """.format(status=status)

        cur = yield self.db.execute(sql, arg)

        data = cur.fetchall()

        return data

    @coroutine
    def fetch_with_code(self, code):
        '''
        :param code: 申请链接的code
        :return: {'cid', 'company_name', 'contact', 'setting'}
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
