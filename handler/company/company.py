__author__ = 'Jon'

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login, require
from utils.general import validate_mobile
from utils.context import catch
from constant import ERR_TIP, MSG, APPLICATION_STATUS, MSG_MODE, DEFAULT_ENTRY_SETTING, MSG_SUB_MODE, RIGHT


class CompanyHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, is_pass):
        """
        @api {get} /api/companies/list/(-?\d+) 公司列表
        @apiName CompanyHandler
        @apiGroup Company

        @apiParam {Number} is_pass -1拒绝, 0审核中, 1通过, 2创始人, 3获取通过的，以及作为创始人的公司列表, 4获取所有和该用户相关的公司列表

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"cid": 1, "company_name": "十全", "create_time": "申请时间", "update_time": "审核时间", "status": "-1拒绝, 0审核中, 1通过"}
                ]
            }        """
        with catch(self):
            is_pass = int(is_pass)
            if is_pass < 0 or is_pass > 4:
                self.error("arg error, check again")
                return

            params = {
                'uid': self.current_user['id'],
                'is_pass': is_pass
            }
            data = yield self.company_service.get_companies(params)

            self.success(data)


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
        with catch(self):
            data = yield self.company_service.select({'id': int(id)})

            self.success(data)


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
        with catch(self):
            # 参数认证
            self.guarantee('name', 'contact', 'mobile')

            validate_mobile(self.params['mobile'])

            # 公司是否存在／是否已经公司员工
            company_info = yield self.company_service.select({'name': self.params['name']}, one=True)

            if company_info:
                err_key = 'company_exists'

                employee_info = yield self.company_employee_service.select({'cid': company_info['id'], 'uid': self.current_user['id']})

                if employee_info: err_key = 'is_employee'

                self.error(status=ERR_TIP[err_key]['sts'], message=ERR_TIP[err_key]['msg'])
                return


            # 创建公司
            del self.params['cid']
            info = yield self.company_service.add(self.params)
            yield self.company_employee_service.add(dict(cid=info['id'], uid=self.current_user['id'], status=APPLICATION_STATUS['founder'], is_admin=1))
            data = {
                'cid': info['id']
            }
            self.success(data)


class CompanyUpdateHandler(BaseHandler):
    @require(RIGHT['modify_company_info'])
    @coroutine
    def post(self):
        """
        @api {post} /api/company/update 更新公司
        @apiName CompanyUpdateHandler
        @apiGroup Company

        @apiUse apiHeader

        @apiParam {Number} cid 公司id
        @apiParam {String} name 公司名称
        @apiParam {String} contact 联系人
        @apiParam {String} mobile 联系方式

        @apiUse Success
        """
        with catch(self):
            # 参数认证
            self.guarantee('cid', 'name', 'contact', 'mobile')

            validate_mobile(self.params['mobile'])

            # 管理员判定
            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            # 公司名字是否存在
            data = yield self.company_service.select(fields='id, name', ut=False, ct=False)
            names = [i['name'] for i in data if i['id'] != self.params['cid']]
            if self.params['name'] in names:
                err_key = 'company_name_repeat'
                self.error(status=ERR_TIP[err_key]['sts'], message=ERR_TIP[err_key]['msg'])
                return

            # 更新数据
            old = {}
            for i in data:
                if i['id'] == self.params['cid']:
                    old = i

            yield self.company_service.update(sets={'name': self.params['name'], 'contact': self.params['contact'], 'mobile': self.params['mobile']},
                                              conds={'id': self.params['cid']},
                                              )
            # 通知
            employee = yield self.company_employee_service.get_employee_list(self.params['cid'], 0, APPLICATION_STATUS['accept'])
            yield self.message_service.notify_change({
                'owners': employee,
                'cid': self.params['cid'],
                'company_name': old['name'],
                'admin_name': self.current_user['name'],
            })
            self.success()


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
        with catch(self):
            cid = int(cid)

            yield self.company_employee_service.check_admin(cid, self.current_user['id'])

            data = yield self.company_entry_setting_service.get_setting(cid)

            self.success(data)

    @require(RIGHT['set_join_conditions'])
    @coroutine
    def post(self, cid):
        """
        @api {post} /api/company/(\d+)/entry/setting 设置员工加入条件
        @apiName CompanyEntrySettingPostHandler
        @apiGroup Company

        @apiUse apiHeader

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
        with catch(self):
            cid = int(cid)

            yield self.company_employee_service.check_admin(cid, self.current_user['id'])

            self.params['cid'] = cid
            url = yield self.company_entry_setting_service.save_setting(self.params)

            self.success({'url': url})


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
        with catch(self):
            cid = int(cid)

            yield self.company_employee_service.check_admin(cid, self.current_user['id'])

            data = yield self.company_entry_setting_service.select(fields='code', conds={'cid': cid}, one=True)

            if not data:
                # 默认配置手机号与姓名
                data = {'cid': cid, 'setting': DEFAULT_ENTRY_SETTING, 'code': self.company_entry_setting_service.create_code(cid)}

                yield self.company_entry_setting_service.add(data)

            self.success({'url': self.company_entry_setting_service.produce_url(data['code'])})


class CompanyApplicationHandler(BaseHandler):
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
        with catch(self):
            if not self.params['code']:
                self.error('缺少code')
                return

            info = yield self.company_service.fetch_with_code(self.params['code'])

            self.success(info)

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
        with catch(self):
            self.guarantee('mobile')

            validate_mobile(self.params['mobile'])

            # 检验code
            info = yield self.company_service.fetch_with_code(self.params['code'])

            if not info:
                self.error('code不合法')
                return

            for f in info['setting'].split(','):
                self.guarantee(f)

            # 加入员工
            app_data = {
                'cid': info['cid'],
                'uid': self.current_user['id']
            }
            yield self.company_employee_service.add_employee(app_data)

            # 给公司管理员发送消息
            admin = yield self.company_employee_service.select(fields='uid', conds={'cid': info['cid'], 'is_admin': 1}, one=True)
            admin_data = {
                'owner': admin['uid'],
                'content': MSG['application']['admin'].format(name=self.params.get('name', ''), mobile=self.params['mobile'], company_name=info['company_name']),
                'mode': MSG_MODE['application'],
                'sub_mode': MSG_SUB_MODE['verify'],
                'tip': '{}:{}'.format(info.get('cid', ''), self.params['code'])
            }

            yield self.message_service.add(admin_data)

            self.success()


class CompanyApplicationVerifyMixin(BaseHandler):
    @coroutine
    def verify(self, mode):
        info = yield self.company_employee_service.get_app_info(self.params['id'])

        yield self.company_employee_service.check_admin(info['cid'], self.current_user['id'])

        yield self.company_employee_service.verify(self.params['id'], mode)

        # 通知用户
        yield self.message_service.notify_verify({
            'owner': info['uid'],
            'admin_name': self.current_user['name'],
            'company_name': info['company_name'],
            'mode': mode,
            'tip': '{}:{}'.format(info.get('cid', ''), info.get('code', ''))
        })


class CompanyApplicationAcceptHandler(CompanyApplicationVerifyMixin):
    @require(RIGHT['audit_employee'])
    @coroutine
    def post(self):
        """
        @api {post} /api/company/application/accept 接受员工申请
        @apiName CompanyApplicationAcceptHandler
        @apiGroup Company

        @apiUse apiHeader

        @apiParam {Number} id 员工表id

        @apiUse Success
        """
        with catch(self):
            yield self.verify('accept')

            self.success()


class CompanyApplicationRejectHandler(CompanyApplicationVerifyMixin):
    @require(RIGHT['audit_employee'])
    @coroutine
    def post(self):
        """
        @api {post} /api/company/application/reject 拒绝员工申请
        @apiName CompanyApplicationRejectHandler
        @apiGroup Company

        @apiUse apiHeader

        @apiParam {Number} id 员工表id

        @apiUse Success
        """
        with catch(self):
            yield self.verify('reject')

            self.success()


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
        with catch(self):
            cid = int(cid)

            employees = yield self.company_employee_service.get_employees(cid)

            self.success(employees)


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
        with catch(self):
            data = yield self.company_employee_service.select({'id': self.params['id'], 'is_admin': 1, 'uid': self.current_user['id']}, one=True)

            if data:
                self.error('管理员不能解除公司，需要先进行管理员转移')
                return

            # 缓存公司信息
            app_info = yield self.company_employee_service.get_app_info(self.params['id'])

            # 解除员工和公司的关系
            yield self.company_employee_service.delete(conds={'id': self.params['id'], 'uid': self.current_user['id']})

            # 将此员工解除公司的消息通知给管理员
            content = MSG['leave']['demission'].format(name=self.current_user['name'],
                                                       mobile=self.current_user['mobile'],
                                                       company_name=app_info['company_name'])
            admin_info = yield self.company_employee_service.select(fields='uid', conds={'cid': app_info['cid'], 'is_admin': 1})
            for info in admin_info:
                yield self.message_service.add({
                    'owner': info['uid'],
                    'content': content,
                    'mode': MSG_MODE['leave']})

            self.success()

class CompanyAdminTransferHandler(BaseHandler):
    @require(RIGHT['set_admin'])
    @coroutine
    def post(self):
        """
        @api {post} /api/company/admin/transfer 转移管理员
        @apiName CompanyAdminTransferHandler
        @apiGroup Company

        @apiUse apiHeader

        @apiParam {Number[]} uids 新管理人员id
        @apiParam {Number} cid 公司id

        @apiUse Success
        """
        with catch(self):
            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            self.params['admin_id'] = self.current_user['id']

            yield self.company_employee_service.transfer_adimin(self.params)

            self.success()


class CompanyApplicationDismissionHandler(BaseHandler):
    @require(RIGHT['dismiss_employee'])
    @coroutine
    def post(self):
        """
        @api {post} /api/company/application/dismission 管理员解除员工
        @apiName CompanyApplicationDismissionHandler
        @apiGroup Company

        @apiUse apiHeader

        @apiParam {Number} id 列表id

        @apiUse Success
        """
        with catch(self):
            data = yield self.company_employee_service.select(fields='cid', conds={'id': self.params['id']}, one=True)

            yield self.company_employee_service.check_admin(data['cid'], self.current_user['id'])

            yield self.company_employee_service.delete({'id': self.params['id']})

            self.success()