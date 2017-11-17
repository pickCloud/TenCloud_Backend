__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import APPLICATION_STATUS, MSG, MSG_MODE, FULL_DATE_FORMAT

class CompanyService(BaseService):
    table  = 'company'
    fields = 'id, name, contact, mobile, description'

    @coroutine
    def get_companies(self, uid):
        ''' 获取个人申请过的公司
        :param uid: 用户id
        :return: [{'cid', 'company_name', 'ctime', 'utime', 'status'}]
        '''
        sql = '''
            SELECT c.id AS cid, c.name AS company_name, DATE_FORMAT(ce.create_time, %s) AS ctime, DATE_FORMAT(ce.update_time, %s) AS utime, ce.status
            FROM company_employee ce
            JOIN company c ON ce.cid = c.id
            WHERE ce.uid = %a
        '''
        cur = yield self.db.execute(sql, [FULL_DATE_FORMAT, FULL_DATE_FORMAT, uid])

        data = cur.fetchall()

        return data


    @coroutine
    def fetch_with_code(self, code):
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

    @coroutine
    def notify_change(self, params):
        ''' 公司信息更改后通知员工
        :param params: {'cid', 'company_name', 'admin_name'}
        '''
        # 所有员工
        sql = '''
            SELECT uid FROM company_employee WHERE cid=%s AND is_admin=%s AND status=%s
        '''
        cur = yield self.db.execute(sql, [params['cid'], 0, APPLICATION_STATUS['accept']])

        employees = cur.fetchall()

        # 通知
        content = MSG['change'].format(company_name=params['company_name'], admin_name=params['admin_name'])

        sql = '''
            INSERT INTO message (owner, content, mode, url) VALUES (%s, %s, %s, %s)
        '''
        for e in employees:
            yield self.db.execute(sql, [e['uid'], content, MSG_MODE['change'], '企业资料页'])

    @coroutine
    def notify_verify(self, params):
        ''' 接受或拒绝员工
        :param params: {'uid', 'company_name', 'admin_name', 'mode'}
        :return:
        '''
        content = MSG['application'][params['mode']].format(company_name=params['company_name'], admin_name=params['admin_name'])

        sql = '''
            INSERT INTO message (owner, content, mode, url) VALUES (%s, %s, %s, %s)
        '''

        yield self.db.execute(sql, [params['uid'], content, MSG_MODE['application'], '企业资料页'])

