import traceback

from tornado.gen import coroutine

from handler.base import BaseHandler
from utils.decorator import is_login


class PermissionResourcesHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, cid):
        """
        @api {get} /api/permission/resource/(\d+)
        @apiName PermissionResourcesHandler
        @apiGroup Permission

        @apiParam {Number} cid 公司id

        @SuccessExample {json} Success-Response
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": 成功,
                "data": {
                    "projects": [
                        {"id": int, "name": str},
                        ...
                    ],
                    "files": [
                        {"id": int, "name": str},
                        ...
                    ],
                    "servers": [
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
    def get(self, ptid):
        """
        @api {get} /api/permission/template/(\d+) 获取权限模版
        @apiName PermissionTemplateHandler
        @apiGroup Permission

        @apiParam {Number} id 权限模版id

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
            ptid = int(ptid)
            data = yield self.permission_template_service.get_template_permission(ptid)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

    @is_login
    @coroutine
    def delete(self, ptid):
        """
        @api {delete} /api/permission/template/(\d+) 删除权限模版
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

            args = ['cid', 'permissions', 'access_servers', 'access_projects', 'access_filehub']
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

            args = ['name', 'cid', 'permissions', 'access_servers', 'access_projects', 'access_filehub']
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
            args = ['cid','name']
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
            data = yield self.permission_service.get_user_permission(cid=cid, uid=uid)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionUserUpdateHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/permission/user/update 更新用户权限详情
        @apiName PermissionUserUpdateHandler
        @apiGroup Permission

        @apiParam {Number} uid 用户id
        @apiParam {Number} cid 公司id
        @apiParam {Number} server_id 服务器id
        @apiParam {Number} project_id 项目id
        @apiParam {Number} filehub_id 文件id
        @apiParam {Number} permission_id 权限id

        @apiUse Success
        """
        try:
            args = ['uid', 'cid']
            self.guarantee(*args)

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            server_ids = self.params.get('server_id', '')
            if server_ids:
                yield self.permission_service.update_user_access_server(self.params)

            project_ids = self.params.get('project_id', '')
            if project_ids:
                yield self.permission_service.update_user_access_project(self.params)

            filehub_ids = self.params.get('filehub_id', '')
            if filehub_ids:
                yield self.permission_service.update_user_access_filehub(self.params)

            permission_ids = self.params.get('permission_id', '')
            if permission_ids:
                yield self.permission_service.update_user_permission(self.params)

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())
