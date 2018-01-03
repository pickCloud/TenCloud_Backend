__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import APPLICATION_STATUS, FULL_DATE_FORMAT
from utils.general import get_in_formats, get_formats


class CompanyEmployeeService(BaseService):
    table  = 'company_employee'
    fields = 'id, cid, uid, is_admin, status'

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
    def add_employee(self, params):
        ''' 添加员工，需先判断员工之前的状态
        :param params: {'cid', 'uid'}
        :return: 审核中或审核通过会抛出异常，已拒绝或新增会更新数据库
        '''
        data = yield self.select(fields='status', conds=['cid=%s', 'uid=%s'], params=[params['cid'], params['uid']], one=True)

        status = data['status'] if data else ''

        if status == APPLICATION_STATUS['process']:
            raise ValueError('您已经提交过申请，正在审核中...')
        elif status in [APPLICATION_STATUS['accept'], APPLICATION_STATUS['founder']]:
            raise ValueError('您已是公司员工，无需再次申请')
        elif status == APPLICATION_STATUS['reject']:
            yield self.update(sets=['status=%s'], conds=['cid=%s', 'uid=%s'], params=[APPLICATION_STATUS['process'], params['cid'], params['uid']])
        else:
            params['status'] = APPLICATION_STATUS['process']
            yield self.add(params)

    @coroutine
    def get_app_info(self, id):
        ''' 通过员工表id获取一些信息
        :param id: 员工表id
        :return: {'company_name', 'cid', 'uid', 'code'}
        '''
        sql = '''
            SELECT c.name AS company_name, c.id AS cid, ce.uid AS uid, ces.code AS code
            FROM company c
            JOIN company_employee ce ON c.id=ce.cid
            JOIN company_entry_setting ces ON c.id=ces.cid
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
            SELECT ce.id, u.id AS uid, u.name, u.mobile, u.image_url,DATE_FORMAT(ce.create_time, %s) AS create_time, DATE_FORMAT(ce.update_time, %s) AS update_time, ce.status, ce.is_admin
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