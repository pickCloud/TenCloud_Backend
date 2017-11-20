import traceback

from tornado.gen import coroutine

from handler.base import BaseHandler
from utils.decorator import is_login


class PermissionTemplateListHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {get} /api/permission/template/list 获取权限模版列表
        @apiName PermissionTemplateListHandler
        @apiGroup Permission

        @apiParam {Number} cid 公司id

        @SuccessExample {json} Success-Response
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
            cid = self.params['cid']
            data = yield self.permission_template_service.select(conds=['cid=%s'], params=[cid])
            self.success(data)

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionTemplateDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, pid):
        """
        @api {get} /api/permission/template/(\d+) 获取权限模版
        @apiName PermissionTemplateDetailHandler
        @apiGroup Permission

        @apiParam {Number} id 权限模版id

        @SuccessExample {json} Success-Response
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
            pid = int(pid)
            data = yield self.permission_template_service.get_template_permission(pid)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

    @is_login
    @coroutine
    def delete(self, pid):
        """
        @api {delete} /api/permission/template/(\d+) 删除权限模版
        @apiName PermissionTemplateDetailHandler
        @apiGroup Permission

        @apiParam {Number} id 权限模版id

        @apiUse Success
        """
        try:

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            pid = int(pid)
            yield self.permission_template_service.delete(conds=['id=%s'], params=[pid])
            self.success()

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionTemplateUpdateHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/permission/template/update 修改权限模版
        @apiName PermissionTemplateUpdateHandler
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

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            id = self.params['id']
            cid = self.params['cid']
            permissions = self.params['permissions']
            access_servers = self.params['access_servers']
            access_projects = self.params['access_projects']
            access_filehub = self.params['access_filehub']

            sets = [
                   'cid=%s', 'permissions=%s',
                   'access_servers=%s','access_projects=%s',
                   'access_filehub=%s'
            ]
            params=[cid, permissions, access_servers, access_projects, access_filehub, id]
            yield self.permission_template_service.update(sets=sets,
                                                        conds=['id=%s'],
                                                        params=params
            )
            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionTemplateRenameHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/permission/template/rename 权限模版重命名
        @apiName PermissionTemplateRenameHandler
        @apiGroup Permission

        @apiParam {Number} id 权限模版id
        @apiParam {String} name 新名字

        @apiUse Success
        """
        try:

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            name, id = self.params['name'], self.params['id']
            yield self.permission_template_service.update(
                                                        sets=['name=%s'],
                                                        conds=['id=%s'],
                                                        params=[name,id]
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


class PermissionUserDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/permission/user/detail 用户权限详情
        @apiName PermissionUserDetailHandler
        @apiGroup Permission

        @apiParam {Number} uid 用户id
        @apiParam {Number} cid 公司id

        @SuccessExample {json} Success-Response
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
            if not(self.params.get('uid', '') or self.params('cid', '')):
                self.error(message='need uid and cid, check again')
                return

            data = yield self.permission_service.get_user_permission(self.params)
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

            yield self.company_employee_service.check_admin(self.params['cid'], self.current_user['id'])

            if not (self.params.get('uid', '') or self.params('cid', '')):
                self.error(message='need uid and cid, check again')
                return

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
