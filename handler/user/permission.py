import traceback

from tornado.gen import coroutine

from handler.base import BaseHandler
from utils.decorator import is_login


class PermissionTemplateList(BaseHandler):
    @coroutine
    @is_login
    def post(self):
        """
        @api {get} /api/usr/permission/list
        @apiName PermissionTemplateList
        @apiGroup User

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


class PermissionTemplateDetail(BaseHandler):
    @coroutine
    @is_login
    def get(self, id):
        """
        @api {post} /api/usr/permission/(\d+)
        @apiName PermissionTemplateDetail
        @apiGroup User

        @apiParam {String} id 权限模版id
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
            data = yield self.permission_template_service.get_permission_detail(id)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

    @coroutine
    @is_login
    def delete(self, id):
        """
        @api {delete} /api/usr/permission/(\d+)
        @apiName PermissionTemplateDetail
        @apiGroup User

        @apiParam {Number} id 权限模版id
        @apiUse Success
        """
        try:
            yield self.permission_template_service.delete(conds=['id=%s'], params=[id])
            self.success()

        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class PermissionTemplateChange(BaseHandler):
    @coroutine
    @is_login
    def post(self):
        """
        @api {post} /api/usr/permission/change
        @apiName PermissionTemplateChange
        @apiGroup User

        @apiParam {Number} id 权限模版id
        @apiParam {Number} cid 公司id
        @apiParam {[]Number} permissions 权限列表
        @apiParam {[]Number} access_servers 服务器列表
        @apiParam {[]Number} access_projects 项目列表
        @apiParam {[]Number} access_filehub 文件列表

        @apiUse Success
        """
        try:
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


class PermissionTemplateRename(BaseHandler):
    @coroutine
    @is_login
    def post(self):
        """
        @api {post} /api/usr/permission/rename
        @apiName PermissionTemplateRename
        @apiGroup User

        @apiParam {Number} id 权限模版id
        @apiParam {String} name 新名字

        @apiUse Success
        """
        try:
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


class PermissionTemplateAdd(BaseHandler):
    @coroutine
    @is_login
    def post(self):
        """
        @api {post} /api/usr/permission/add
        @apiName PermissionTemplateAdd
        @apiGroup User

        @apiParam {String} name 名字
        @apiParam {Number} cid 公司id
        @apiParam {[]Number} permissions 权限列表
        @apiParam {[]Number} access_servers 服务器列表
        @apiParam {[]Number} access_projects 项目列表
        @apiParam {[]Number} access_filehub 文件列表

        @apiUse Success
        """
        try:
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
