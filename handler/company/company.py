__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login
from utils.general import validate_mobile
from constant import ERR_TIP, MSG, APPLICATION_STATUS, MSG_MODE, DEFAULT_ENTRY_SETTING


class CompanyHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/companies 公司列表
        @apiName CompanyHandler
        @apiGroup Company

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"cid": 1, "company_name": "十全", "ctime": "申请时间", "utime": "审核时间", "status": "-1拒绝, 0审核中, 1通过"}
                ]
            }        """
        try:
            data = yield self.company_service.get_companies(self.current_user['id'])

            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyDetailHandler(BaseHandler):
    @coroutine
    def get(self, id):
        """
        @api {get} /api/company/(\d+) 公司详情
        @apiName CompanyDetailHandler
        @apiGroup Company

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"id": 1, "name": "十全", "create_time": "申请时间", "update_time": "审核时间", "contact": "联系人", "mobile": "手机号", "description": "公司简介"}
                ]
            }        """
        try:
            data = yield self.company_service.select(conds=['id=%s'], params=[id])

            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyNewHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/company/new 创建公司
        @apiName CompanyNewHandler
        @apiGroup Company

        @apiParam {String} name 公司名称
        @apiParam {String} contact 联系人
        @apiParam {String} mobile 联系方式

        @apiErrorExample {json} Error-Response:
        HTTP/1.1 400
            {
                "status": 10000/10001,
                "message": 公司已存在/公司已存在并且是员工,
                "data": {}
            }
        """
        try:
            # 参数认证
            self.guarantee('name', 'contact', 'mobile')

            validate_mobile(self.params['mobile'])

            # 公司是否存在／是否已经公司员工
            company_info = yield self.company_service.select(conds=['name=%s'], params=[self.params['name']], one=True)

            if company_info:
                err_key = 'company_exists'

                employee_info = yield self.company_employee_service.select(conds=['cid=%s', 'uid=%s'], params=[company_info['id'], self.current_user['id']])

                if employee_info: err_key = 'is_employee'

                self.error(status=ERR_TIP[err_key]['sts'], message=ERR_TIP[err_key]['msg'])
                return


            # 创建公司
            info = yield self.company_service.add(self.params)
            yield self.company_employee_service.add(dict(cid=info['id'], uid=self.current_user['id'], status=APPLICATION_STATUS['accept'], is_admin=1))

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyUpdateHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/company/update 更新公司
        @apiName CompanyUpdateHandler
        @apiGroup Company

        @apiParam {Number} cid 公司id
        @apiParam {String} name 公司名称
        @apiParam {String} contact 联系人
        @apiParam {String} mobile 联系方式

        @apiUse Success
        """
        try:
            # 参数认证
            self.guarantee('cid', 'name', 'contact', 'mobile')

            validate_mobile(self.params['mobile'])

            # 管理员判定
            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            # 更新数据
            old = yield self.company_service.select(fields='name', conds=['id=%s'], params=[self.params['cid']], one=True)

            yield self.company_service.update(sets=['name=%s', 'contact=%s', 'mobile=%s'],
                                              conds=['id=%s'],
                                              params=[self.params['name'], self.params['contact'], self.params['mobile'], self.params['cid']])

            # 通知
            yield self.company_service.notify_change({
                'cid': self.params['cid'],
                'company_name': old['name'],
                'admin_name': self.current_user['name'],
            })

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyEntrySettingHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid):
        """
        @api {get} /api/company/(\d+)/entry/setting 获取员工加入条件
        @apiName CompanyEntrySettingGetHandler
        @apiGroup Company

        @apiParam {Number} cid     公司id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "url": "https://c.10.com/#/invite?code=65d4a0f"
                }
            }

        @apiErrorExample {json} Error-Response:
        HTTP/1.1 400
            {
                "status": 1,
                "msg": "需要管理员权限",
                "data": {}
            }
        """
        try:
            cid = int(cid)

            yield self.company_employee_service.check_admin(cid, self.current_user['id'])

            data = yield self.company_entry_setting_service.get_setting(cid)

            self.success(data)

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

    @is_login
    @coroutine
    def post(self, cid):
        """
        @api {post} /api/company/(\d+)/entry/setting 设置员工加入条件
        @apiName CompanyEntrySettingPostHandler
        @apiGroup Company

        @apiParam {String} setting 配置mobile,name,id_card

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "url": "https://c.10.com/#/invite?code=65d4a0f"
                }
            }

        @apiErrorExample {json} Error-Response:
        HTTP/1.1 400
            {
                "status": 1,
                "msg": "需要管理员权限",
                "data": {}
            }
        """
        try:
            cid = int(cid)

            yield self.company_employee_service.check_admin(cid, self.current_user['id'])

            self.params['cid'] = cid
            url = yield self.company_entry_setting_service.save_setting(self.params)

            self.success({'url': url})

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyEntryUrlHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid):
        """
        @api {get} /api/company/(\d+)/entry/url 获取员工加入URL
        @apiName CompanyEntryUrlHandler
        @apiGroup Company

        @apiParam {String} cid     公司id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "url": "https://c.10.com/#/invite?code=65d4a0f"
                }
            }

        @apiErrorExample {json} Error-Response:
        HTTP/1.1 400
            {
                "status": 1,
                "msg": "需要管理员权限",
                "data": {}
            }
        """
        try:
            cid = int(cid)

            yield self.company_employee_service.check_admin(cid, self.current_user['id'])

            data = yield self.company_entry_setting_service.select(fields='code', conds=['cid=%s'], params=[cid], one=True)

            if not data:
                # 默认配置手机号与姓名
                data = {'cid': cid, 'setting': DEFAULT_ENTRY_SETTING, 'code': self.company_entry_setting_service.create_code(cid)}

                yield self.company_entry_setting_service.add(data)

            self.success({'url': self.company_entry_setting_service.produce_url(data['code'])})

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyApplicationHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/company/application 员工申请加入的初始条件
        @apiName CompanyApplicationGetHandler
        @apiGroup Company

        @apiParam {String} code

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "company_name": "十全",
                    "contact": "13900000000",
                    "setting": "mobile,name"
                }
            }
        """
        try:
            code = self.get_argument('code')

            if not code:
                self.error('缺少code')
                return

            info = yield self.company_service.fetch_with_code(code)

            self.success(info)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/company/application 员工申请提交
        @apiName CompanyApplicationPostHandler
        @apiGroup Company

        @apiParam {String} code
        @apiParam {String} mobile
        @apiParam {String} name 可选
        @apiParam {String} id_card 可选

        @apiUse Success
        """
        try:
            self.guarantee('mobile')

            validate_mobile(self.params['mobile'])

            # 检验code
            info = yield self.company_service.fetch_with_code(self.params['code'])

            if not info:
                self.error('code不合法')
                return

            for f in info['setting'].split(','):
                self.guarantee(f)

            # 是否申请中或已通过
            yield self.company_employee_service.pre_application(info['cid'], self.current_user['id'])

            # 加入员工
            app_data = {
                'cid': info['cid'],
                'uid': self.current_user['id'],
                'status': APPLICATION_STATUS['process']
            }
            yield self.company_employee_service.add(app_data)

            # 给公司管理员发送消息
            admin = yield self.company_employee_service.select(fields='uid', conds=['cid=%s', 'is_admin=%s'], params=[info['cid'], 1], one=True)

            admin_data = {
                'owner': admin['uid'],
                'content': MSG['application']['admin'].format(name=self.params.get('name', ''), mobile=self.params['mobile'], company_name=info['company_name']),
                'url': '企业资料的员工管理界面',
                'mode': MSG_MODE['application']
            }

            yield self.message_service.add(admin_data)

            self.success()

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyApplicationVerifyMixin(BaseHandler):
    @coroutine
    def verify(self, mode):
        info = yield self.company_employee_service.get_app_info(self.params['id'])

        yield self.company_employee_service.check_admin(info['cid'], self.current_user['id'])

        yield self.company_employee_service.verify(self.params['id'], mode)

        yield self.company_service.notify_verify({
            'uid': info['uid'],
            'admin_name': self.current_user['name'],
            'company_name': info['company_name'],
            'mode': mode
        })


class CompanyApplicationAcceptHandler(CompanyApplicationVerifyMixin):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/company/application/accept 接受员工申请
        @apiName CompanyApplicationAcceptHandler
        @apiGroup Company

        @apiParam {Number} id 员工表id

        @apiUse Success
        """
        try:
            yield self.verify('accept')

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyApplicationRejectHandler(CompanyApplicationVerifyMixin):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/company/application/reject 拒绝员工申请
        @apiName CompanyApplicationRejectHandler
        @apiGroup Company

        @apiParam {Number} id 员工表id

        @apiUse Success
        """
        try:
            yield self.verify('reject')

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyEmployeeHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid):
        """
        @api {get} /api/company/(\d+)/employees 获取员工列表
        @apiName CompanyEmployeeHandler
        @apiGroup Company

        @apiUse Success
        """
        try:
            cid = int(cid)

            yield self.company_employee_service.check_employee(cid, self.current_user['id'])

            employees = yield self.company_employee_service.get_employees(cid)

            self.success(employees)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyEmployeeDismissionHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/company/employee/dismission 员工解除公司
        @apiName CompanyEmployeeHandler
        @apiGroup Company

        @apiParam {Number} id 列表id

        @apiUse Success
        """
        try:
            data = yield self.company_employee_service.select(conds=['id=%s','is_admin=%s', 'uid=%s'],
                                                              params=[self.params['id'], 1, self.current_user['id']])

            if data:
                self.error('管理员不能解除公司，需要先进行管理员转移')
                return

            yield self.company_employee_service.delete(conds=['id=%s', 'uid=%s'], params=[self.params['id'], self.current_user['id']])

            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyAdminTransferHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/company/admin/transfer 转移管理员
        @apiName CompanyAdminTransferHandler
        @apiGroup Company

        @apiParam {Number[]} uids 新管理人员id
        @apiParam {Number} cid 公司id

        @apiUse Success
        """
        try:
            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            self.params['admin_id'] = self.current_user['id']

            yield self.company_employee_service.transfer_adimin(self.params)

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class CompanyApplicationDismissionHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/company/application/dismission 管理员解除员工
        @apiName CompanyApplicationDismissionHandler
        @apiGroup Company

        @apiParam {Number} id 列表id

        @apiUse Success
        """
        try:
            data = yield self.company_employee_service.select(fields='cid', conds=['id=%s'], params=[self.params['id']], one=True)

            yield self.company_employee_service.check_admin(data['cid'], self.current_user['id'])

            yield self.company_employee_service.delete(conds=['id=%s'], params=[self.params['id']])

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())