__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import APPLICATION_STATUS, MSG, MSG_MODE, FULL_DATE_FORMAT, MSG_SUB_MODE

class CompanyService(BaseService):
    table  = 'company'
    fields = 'id, name, contact, mobile, description'

    @coroutine
    def get_companies(self, params):
        ''' 获取个人申请过的公司
        :param uid: 用户id
        :return: [{'cid', 'company_name', 'create_time', 'update_time', 'status'}]
        '''

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
            SELECT c.id AS cid, c.name AS company_name, ce.is_admin AS is_admin,
                   DATE_FORMAT(ce.create_time, %s) AS create_time, DATE_FORMAT(ce.update_time, %s) AS update_time, ce.status
            FROM company_employee ce
            JOIN company c ON ce.cid = c.id
            WHERE ce.uid = %s {status}
        """.format(status=status)
        cur = yield self.db.execute(sql, arg)
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
            INSERT INTO message (owner, content, mode, sub_mode, tip) VALUES (%s, %s, %s, %s, %s)
        '''
        for e in employees:
            yield self.db.execute(sql, [e['uid'], content, MSG_MODE['change'], MSG_SUB_MODE['change'], '{}:'.format(params['cid'])])

    @coroutine
    def notify_verify(self, params):
        ''' 接受或拒绝员工
        :param params: {'uid', 'company_name', 'admin_name', 'mode', 'sub_mode', 'tip'}
        :return:
        '''
        content = MSG['application'][params['mode']].format(company_name=params['company_name'], admin_name=params['admin_name'])

        sql = '''
            INSERT INTO message (owner, content, mode, sub_mode, tip) VALUES (%s, %s, %s, %s, %s)
        '''

        yield self.db.execute(sql, [params['uid'], content, MSG_MODE['application'], params['sub_mode'], params['tip']])

