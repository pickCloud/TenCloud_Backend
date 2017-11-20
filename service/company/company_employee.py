__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import APPLICATION_STATUS, FULL_DATE_FORMAT
from utils.general import get_in_formats


class CompanyEmployeeService(BaseService):
    table  = 'company_employee'
    fields = 'id, cid, uid, is_admin'

    @coroutine
    def check_admin(self, cid, uid):
        ''' 是否管理员
        :param cid: 公司id
        :param uid: 用户id
        '''
        data = yield self.select(conds=['cid=%s', 'uid=%s', 'is_admin=%s'], params=[cid, uid, 1], one=True)

        if not data:
            raise ValueError('需要管理员权限')

    @coroutine
    def check_employee(self, cid, uid):
        ''' 是否公司员工
        :param cid: 公司id
        :param uid: 用户id
        '''
        data = yield self.select(conds=['cid=%s', 'uid=%s'], params=[cid, uid], one=True)

        if not data:
            raise ValueError('非公司员工')

    @coroutine
    def pre_application(self, cid, uid):
        ''' 提交申请前检验
        :param cid: 公司id
        :param uid: 用户id
        :return: 审核中或审核通过会抛出异常
        '''
        in_process = yield self.select(conds=['cid=%s', 'uid=%s', 'status=%s'], params=[cid, uid, APPLICATION_STATUS['process']])

        if in_process:
            raise ValueError('您已经提交过申请，正在审核中...')

        is_accept = yield self.select(conds=['cid=%s', 'uid=%s', 'status=%s'], params=[cid, uid, APPLICATION_STATUS['accept']])

        if is_accept:
            raise ValueError('您已是公司员工，无需再次申请')

    @coroutine
    def get_app_info(self, id):
        ''' 通过员工表id获取一些信息
        :param id: 员工表id
        :return: {'company_name', 'cid', 'uid'}
        '''
        sql = '''
            SELECT c.name AS company_name, c.id AS cid, ce.uid AS uid
            FROM company c
            JOIN company_employee ce ON c.id=ce.cid
            WHERE ce.id=%s
        '''
        cur = yield self.db.execute(sql, id)

        info = cur.fetchone()

        return info

    @coroutine
    def verify(self, id, mode):
        ''' 通过或拒绝员工
        :param id: 员工表id
        :param mode: APPLICATION_STATUS的key
        '''
        is_repeat = yield self.select(conds=['id=%s', 'status=%s'], params=[id, APPLICATION_STATUS[mode]])

        if is_repeat:
            raise ValueError('请勿重复操作')

        yield self.update(sets=['status=%s'], conds=['id=%s'], params=[APPLICATION_STATUS[mode], id])

    @coroutine
    def get_employees(self, cid):
        ''' 获取员工列表
        :param cid: 公司id
        '''
        sql = '''
            SELECT ce.id, u.name, u.mobile, DATE_FORMAT(ce.create_time, %s) AS ctime, DATE_FORMAT(ce.update_time, %s) AS utime, ce.status, ce.is_admin
            FROM company_employee ce
            JOIN user u ON ce.uid = u.id
            WHERE ce.cid = %s
        '''
        cur = yield self.db.execute(sql, [FULL_DATE_FORMAT, FULL_DATE_FORMAT, cid])
        data = cur.fetchall()

        return data

    @coroutine
    def transfer_adimin(self, params):
        ''' 转换管理员
        :param params: {'admin_id', 'cid', 'uids'}
        '''
        yield self.update(sets=['is_admin=%s'], conds=['uid=%s', 'cid=%s'], params=[0, params['admin_id'], params['cid']])

        yield self.update(sets=['is_admin=%s'],
                          conds=[get_in_formats('uid', params['uids']), 'cid=%s'],
                          params=[1] + params['uids'] + [params['cid']])