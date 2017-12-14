import traceback

from tornado.gen import coroutine, Task

from handler.base import BaseHandler
from utils.decorator import is_login
from constant import COMPANY_PERMISSION, USER_PERMISSION, PERMISSIONS_FLAG

class PermissionResourcesHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid):
        """
        @api {get} /api/permission/resource/(\d+)
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
                        {"id": int, "name": str},
                        ...
                    ],
                    "access_servers": [
                        {"id": int, "name": str},
                        ..
                    ],
                }
            }
        """
        try:
            cid = int(cid)
            data = yield self.permission_template_service.get_resources(cid)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


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
        try:
            cid = int(cid)
            data = yield self.permission_template_service.select(conds=['cid=%s'], params=[cid])
            self.success(data)

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


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
        try:
            params = {
                'id': int(pt_id),
                'format': int(pt_format)
            }
            data = yield self.permission_template_service.get_template_permission(params)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

    @is_login
    @coroutine
    def post(self, ptid):
        """
        @api {post} /api/permission/template/(\d+) 删除权限模版
        @apiName PermissionTemplateHandler
        @apiGroup Permission

        @apiParam {Number} id 权限模版id
        @apiParam {Number} cid 公司id

        @apiUse Success
        """
        try:

            args = ['cid']
            self.guarantee(*args)

            ptid = int(ptid)

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            yield self.permission_template_service.delete(conds=['id=%s'], params=[ptid])
            self.success()

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

    @is_login
    @coroutine
    def put(self, ptid):
        """
        @api {pu} /api/permission/template/(\d+) 修改权限模版
        @apiName PermissionTemplateHandler
        @apiGroup Permission

        @apiParam {Number} id 权限模版id
        @apiParam {Number} cid 公司id
        @apiParam {[]Number} permissions 权限列表
        @apiParam {[]Number} access_servers 服务器列表
        @apiParam {[]Number} access_projects 项目列表
        @apiParam {[]Number} access_filehub 文件列表

        @apiUse Success
        """
        try:

            args = ['cid']
            self.guarantee(*args)

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            ptid = int(ptid)
            permissions = self.params['permissions']
            access_servers = self.params['access_servers']
            access_projects = self.params['access_projects']
            access_filehub = self.params['access_filehub']

            sets = [
                'permissions=%s',
                'access_servers=%s', 'access_projects=%s',
                'access_filehub=%s'
            ]
            params = [permissions, access_servers, access_projects, access_filehub, ptid]
            yield self.permission_template_service.update(sets=sets,
                                                          conds=['id=%s'],
                                                          params=params
                                                          )
            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionTemplateAddHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/permission/template/add 增加权限模版
        @apiName PermissionTemplateAddHandler
        @apiGroup Permission

        @apiParam {String} name 名字
        @apiParam {Number} cid 公司id
        @apiParam {[]Number} permissions 权限列表
        @apiParam {[]Number} access_servers 服务器列表
        @apiParam {[]Number} access_projects 项目列表
        @apiParam {[]Number} access_filehub 文件列表

        @apiUse Success
        """
        try:
            args = ['name', 'cid']
            self.guarantee(*args)

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            params = {
                'name': self.params['name'],
                'cid': self.params['cid'],
                'permissions': self.params['permissions'],
                'access_servers': self.params['access_servers'],
                'access_projects': self.params['access_projects'],
                'access_filehub': self.params['access_filehub']
            }

            yield self.permission_template_service.add(params)
            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionTemplateRenameHandler(BaseHandler):
    @is_login
    @coroutine
    def put(self, ptid):
        """
        @api {post} /api/permission/template/(\d+)/rename 权限模版重命名
        @apiName PermissionTemplateRenameHandler
        @apiGroup Permission

        @apiParam {Number} id 权限模版id
        @apiParam {Number} cid 公司id
        @apiParam {String} name 新名字

        @apiUse Success
        """
        try:
            args = ['cid', 'name']
            self.guarantee(*args)

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            name, ptid = self.params['name'], int(ptid)
            yield self.permission_template_service.update(
                                                        sets=['name=%s'],
                                                        conds=['id=%s'],
                                                        params=[name, ptid]
            )
            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionUserDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid, uid):
        """
        @api {get} /api/permission/(\d+)/user/(\d+)/detail 用户权限详情
        @apiName PermissionUserDetailHandler
        @apiGroup Permission

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
        try:
            cid, uid = int(cid), int(uid)

            company_user = USER_PERMISSION.format(cid=cid, uid=uid)
            has_set = yield Task(self.redis.hget, COMPANY_PERMISSION, company_user)
            if not has_set:
                data = {
                    'access_servers': '',
                    'access_projects': '',
                    'access_filehub': '',
                    'permission': '',
                }
                self.success(data)
                return

            data = yield self.permission_service.get_user_permission(cid=cid, uid=uid)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionUserUpdateHandler(BaseHandler):

    def deal_args(self, object_str):
        arg = {
            'table': '',
            'fields': '',
            'uid': self.params['uid'],
            'cid': self.params['cid'],
            'data': '',
        }
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

        @apiParam {Number} uid 用户id
        @apiParam {Number} cid 公司id
        @apiParam {String} access_servers 服务器id 如: "1,2,3"
        @apiParam {String} access_projects 项目id 如上
        @apiParam {String} access_filehub 文件id  如上
        @apiParam {String} permissions 权限id 如上

        @apiUse Success
        """
        try:
            args = ['uid', 'cid']
            self.guarantee(*args)

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            access_servers = self.params.get('access_servers', '')
            if access_servers:
                arg = self.deal_args(access_servers)
                arg['table'] = 'user_access_server'
                arg['fields'] = '(`uid`, `sid`, `cid`)'
                yield self.permission_service.update_user(arg)

            access_projects = self.params.get('access_projects', '')
            if access_projects:
                arg = self.deal_args(access_projects)
                arg['table'] = 'user_access_project'
                arg['fields'] = '(`uid`, `pid`, `cid`)'
                yield self.permission_service.update_user(arg)

            access_filehub = self.params.get('access_filehub', '')
            if access_filehub:
                arg = self.deal_args(access_filehub)
                arg['table'] = 'user_access_filehub'
                arg['fields'] = '(`uid`, `fid`, `cid`)'
                yield self.permission_service.update_user(arg)

            permissions = self.params.get('permissions', '')
            if permissions:
                arg = self.deal_args(permissions)
                arg['table'] = 'user_permission'
                arg['fields'] = '(`uid`, `pid`, `cid`)'
                yield self.permission_service.update_user(arg)

            company_user = USER_PERMISSION.format(cid=self.params['cid'], uid=self.params['uid'])
            yield Task(self.redis.hset, COMPANY_PERMISSION, company_user, PERMISSIONS_FLAG)

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())
