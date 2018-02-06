from tornado.gen import coroutine, Task

from handler.base import BaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from constant import COMPANY_PERMISSION, USER_PERMISSION, PERMISSIONS_FLAG, PERMISSIONS_NOTIFY_FLAG, RIGHT, \
    PERMISSIONS_TEMPLATE_TYPE, ERR_TIP, PT_FORMAT


class PermissionResourcesHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid):
        """
        @api {get} /api/permission/resource/(\d+) 获取所有模版资源

        @apiName PermissionResourcesHandler
        @apiGroup Permission

        @apiParam {Number} cid 公司id

        @apiSuccessExample {json} Success-Response
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": 成功,
                "data": {
                    "access_projects": [
                        {"id": int, "name": str},
                        ...
                    ],
                    "access_files": [
                        {"id": int, "name": str, "type": 0表示文件, 1表示文件夹},
                        ...
                    ],
                    "access_servers": [
                        {"id": int, "name": str},
                        ..
                    ],
                }
            }
        """
        with catch(self):
            cid = int(cid)
            data = yield self.permission_template_service.get_resources(cid)
            self.success(data)


class PermissionTemplateListHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid):
        """
        @api {get} /api/permission/template/list/(\d+) 获取权限模版列表
        @apiName PermissionTemplateListHandler
        @apiGroup Permission

        @apiParam {Number} cid 公司id

        @apiSuccessExample {json} Success-Response
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": 成功,
                "data": [
                    ...
                ]
            }
        """
        with catch(self):
            cid = int(cid)
            data = yield self.permission_template_service.select({'cid': cid})
            data = yield self.permission_template_service.check_pt_exist(data)
            preset = yield self.permission_template_service.get_admin(cid)
            res = [preset]
            if data:
                if isinstance(data, list):
                    res.extend(data)
                else:
                    res = [preset, data]
            self.success(res)


class PermissionTemplateHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, pt_id, pt_format):
        """
        @api {get} /api/permission/template/(\d+)/format/(\d+) 获取权限模版
        @apiName PermissionTemplateHandler
        @apiGroup Permission

        @apiParam {Number} pt_id 权限模版id
        @apiParam {Number} pt_format 模版样式(差别为是否格式化) 0:标准 1:简单

        @apiSuccessExample {json} Success-Response
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": 成功,
                "data": [
                    ...
                ]
            }
        """
        with catch(self):
            params = {
                'id': int(pt_id),
                'format': int(pt_format)
            }
            data = yield self.permission_template_service.get_template_permission(params)
            self.success(data)


class PermissionTemplateAddHandler(BaseHandler):
    @require(RIGHT['add_permission_template'])
    @coroutine
    def post(self):
        """
        @api {post} /api/permission/template/add 增加权限模版
        @apiName PermissionTemplateAddHandler

        @apiGroup Permission

        @apiUse cidHeader

        @apiParam {String} name 名字
        @apiParam {Number} cid 公司id
        @apiParam {String} permissions 权限列表 如: "1,2,3"
        @apiParam {String} access_servers 服务器列表 如上
        @apiParam {String} access_projects 项目列表 如上
        @apiParam {String} access_filehub 文件列表  如上

        @apiUse Success
        """

        with catch(self):
            args = ['cid','name']
            self.guarantee(*args)

            sets = {
                'cid': self.params['cid'],
                'name': self.params['name'],
                'permissions': self.params['permissions'],
                'access_projects': self.params['access_projects'],
                'access_servers': self.params['access_servers'],
                'access_filehub': self.params['access_filehub']
            }
            yield self.permission_template_service.add(sets)
            
            self.success()


class PermissionTemplateDelHandler(BaseHandler):
    @require(RIGHT['delete_permission_template'])
    @coroutine
    def post(self, pt_id):
        """
        @api {post} /api/permission/template/(\d+)/del 删除权限模版
        @apiName PermissionTemplateDelHandler

        @apiGroup Permission
        @apiUse cidHeader

        @apiParam {Number} pt_id 权限模版id
        @apiParam {Number} cid 公司id

        @apiUse Success
        """
        with catch(self):
            args = ['cid']
            self.guarantee(*args)
            pt_id = int(pt_id)

            pt_info = yield self.permission_template_service.select({'id': pt_id}, one=True)
            if pt_info['type'] == PERMISSIONS_TEMPLATE_TYPE['default']:
                err_key = 'permission_template_cannot_operate'
                self.error(status=ERR_TIP[err_key]['sts'], message=ERR_TIP[err_key]['msg'])
                return

            yield self.permission_template_service.delete({'id': pt_id})
  
            self.success()


class PermissionTemplateRenameHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self, pt_id):
        """
        @api {post} /api/permission/template/(\d+)/rename 权限模版重命名
        @apiName PermissionTemplateRenameHandler
        @apiGroup Permission

        @apiParam {Number} pt_id 权限模版id
        @apiParam {Number} cid 公司id
        @apiParam {String} name 新名字

        @apiUse Success
        """

        with catch(self):
            args = ['name', 'cid']
            self.guarantee(*args)

            name, pt_id = self.params['name'], int(pt_id)
            yield self.permission_template_service.update(sets={'name': name}, conds={'id': pt_id})

            self.success()


class PermissionTemplateUpdateHandler(BaseHandler):
    @require(RIGHT['modify_permission_template'])
    @coroutine
    def put(self, pt_id):
        """
        @api {put} /api/permission/template/(\d+)/update 修改权限模版
        @apiName PermissionTemplateUpdateHandler
        @apiGroup Permission

        @apiUse cidHeader

        @apiParam {Number} pt_id 权限模版id
        @apiParam {Number} cid 公司id
        @apiParam {String} name 名字
        @apiParam {String} permissions 权限列表 如: "1,2,3"
        @apiParam {String} access_servers 服务器列表 如上
        @apiParam {String} access_projects 项目列表 如上
        @apiParam {String} access_filehub 文件列表 如上

        @apiUse Success
        """

        with catch(self):
            args = ['cid']

            self.guarantee(*args)

            pt_id = int(pt_id)

            pt_info = yield self.permission_template_service.select({'id': pt_id}, one=True)
            if pt_info['type'] == PERMISSIONS_TEMPLATE_TYPE['default']:
                err_key = 'permission_template_cannot_operate'
                self.error(status=ERR_TIP[err_key]['sts'], message=ERR_TIP[err_key]['msg'])
                return

            sets = {}

            if self.params.get('name', pt_info['name']):
                sets.update({'name':self.params['name']})

            if self.params.get('permissions', ''):
                sets.update({'permissions': self.params['permissions']})

            if self.params.get('access_servers', ''):
                sets.update({'access_servers': self.params['access_servers']})

            if self.params.get('access_projects', ''):
                sets.update({'access_projects': self.params['access_projects']})

            if self.params.get('access_filehub', ''):
                sets.update({'access_filehub': self.params['access_filehub']})

            yield self.permission_template_service.update(sets=sets, conds={'id': pt_id})

            self.success()


class PermissionUserDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid, uid, pt_format):
        """
        @api {get} /api/permission/(\d+)/user/(\d+)/detail/format/(\d+) 用户权限详情
        @apiName PermissionUserDetailHandler
        @apiGroup Permission

        @apiParam {Number} cid 公司id
        @apiParam {Number} uid 公司id
        @apiParam {Number} pt_format 模版样式(差别为是否格式化) 0:标准 1:简单

        @apiSuccessExample {json} Success-Response
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": 成功,
                "data": [
                    ...
                ]
            }
        """
        with catch(self):
            cid, uid, pt_format = int(cid), int(uid), int(pt_format)
            yield self.company_employee_service.check_staff(cid=cid, uid=uid)

            params = {
                'uid': uid,
                'cid': cid,
                'format': pt_format
            }

            data = {
                    'access_servers': [],
                    'access_projects': [],
                    'access_filehub': [],
                    'permissions': [],
                }

            if params['format'] == PT_FORMAT['standard']:
                data = [
                            {
                                'name': '功能',
                                'data': []
                            },
                            {
                                'name': '数据',
                                'data': [
                                    {
                                        'name': '文件仓库',
                                        'data': [
                                            {'name': '文件仓库', 'data': []}
                                        ]
                                    },
                                    {
                                        'name': '项目管理',
                                        'data': [
                                            {'name': '项目管理', 'data': []}
                                        ]
                                    },
                                    {
                                        'name': '云服务器',
                                        'data': []
                                    }
                                ]
                            }
                    ]
            company_user = USER_PERMISSION.format(cid=cid, uid=uid)
            has_set = self.redis.hget(COMPANY_PERMISSION, company_user)
            if not has_set:
                self.success(data)
                return

            data = yield self.permission_service.get_user_permission(params)
            self.success(data)


class PermissionUserUpdateHandler(BaseHandler):

    def deal_args(self, object_str):
        arg = {
            'table': '',
            'fields': '',
            'uid': self.params['uid'],
            'cid': self.params['cid'],
            'data': '',
        }
        if not object_str:
            return arg

        data = []
        for k in object_str.split(','):
            value = '(' + str(self.params['uid']) + ',' + k + ',' + str(self.params['cid']) + ')'
            data.append(value)
        arg['data'] = ','.join(data)
        return arg

    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/permission/user/update 更新用户权限详情
        @apiName PermissionUserUpdateHandler
        @apiGroup Permission

        @apiUse cidHeader

        @apiParam {Number} uid 用户id
        @apiParam {Number} cid 公司id
        @apiParam {String} access_servers 服务器id 如: "1,2,3"
        @apiParam {String} access_projects 项目id 如上
        @apiParam {String} access_filehub 文件id  如上
        @apiParam {String} permissions 权限id 如上

        @apiUse Success
        """
        with catch(self):
            args = ['uid', 'cid']
            self.guarantee(*args)

            # 只有管理员才可以修改员工的权限
            yield self.company_employee_service.check_admin(self.params.get('cid'), self.current_user['id'])

            yield self.company_employee_service.check_staff(cid=self.params.get('cid'), uid=self.params.get('uid'))

            arg = self.deal_args(self.params['access_servers'])
            arg['table'] = 'user_access_server'
            arg['fields'] = '(`uid`, `sid`, `cid`)'
            yield self.permission_service.update_user(arg)

            arg = self.deal_args(self.params['access_projects'])
            arg['table'] = 'user_access_project'
            arg['fields'] = '(`uid`, `pid`, `cid`)'
            yield self.permission_service.update_user(arg)

            arg = self.deal_args(self.params['access_filehub'])
            arg['table'] = 'user_access_filehub'
            arg['fields'] = '(`uid`, `fid`, `cid`)'
            yield self.permission_service.update_user(arg)

            arg = self.deal_args(self.params['permissions'])
            arg['table'] = 'user_permission'
            arg['fields'] = '(`uid`, `pid`, `cid`)'
            yield self.permission_service.update_user(arg)

            company_user = USER_PERMISSION.format(cid=self.params['cid'], uid=self.params['uid'])
            self.redis.hset(COMPANY_PERMISSION, company_user, PERMISSIONS_FLAG | PERMISSIONS_NOTIFY_FLAG)

            self.success()