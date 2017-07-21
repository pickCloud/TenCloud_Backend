__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.general import get_in_formats
from setting import settings
from constant import FULL_DATE_FORMAT


class ProjectHandler(BaseHandler):
    @coroutine
    def get(self):
        """
        @api {get} /api/projects 获取项目列表
        @apiName ProjectHandler
        @apiGroup Project

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": [
                {
                    "id": int,
                    "name": str,
                    "description": str,
                    "repos_name": str,
                    "repos_url": str,
                    "update_time": str,
                    "status": str,
                }
                    ...
                ]
            }
        """
        try:
            result = yield self.project_service.select(ct=False)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectNewHandler(BaseHandler):
    @coroutine
    def post(self):
        """
        @api {post} /api/project/new 创建新项目
        @apiName ProjectNewHandler
        @apiGroup Project

        @apiParam {String} name 名称(必需小写字母，分隔符可选),
        @apiParam {String} description 描述
        @apiParam {String} repos_name 仓库名称
        @apiParam {String} repos_url 仓库url
        @apiParam {Number} mode 类型

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "id": int,
                    "update_time": str
                }
            }
        """

        try:
            is_duplicate_url = yield self.project_service.select(conds=['repos_url=%s'], params=[self.params['repos_url']], one=True)

            if is_duplicate_url:
                self.error('仓库url重复')
                return

            result = yield self.project_service.add(params=self.params)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectDelHandler(BaseHandler):
    @coroutine
    def post(self):
        """
        @api {post} /api/project/del 项目删除
        @apiName ProjectDelHandler
        @apiGroup Project

        @apiParam {number[]} id 项目id

        @apiUse Success
        """
        try:
            ids = self.params['id']

            yield self.project_service.delete(conds=[get_in_formats('id', ids)], params=ids)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectDetailHandler(BaseHandler):
    @coroutine
    def get(self, id):
        """
        @api {get} /api/project/(\d+) 项目详情
        @apiName ProjectDetailHandler
        @apiGroup Project

        @apiParam {Number} id 项目id

        @apiSuccessExample {json} Success-Response
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": [
                {
                    "description": str,
                    "repos_name": str,
                    "repos_url": str,
                    "id": 2,
                    "name": str,
                    "create_time": str,
                    "update_time": str,
                    "status": str,
                    "mode": str
                }
                    ...
                ]
            }
        """
        try:
            result = yield self.project_service.select(conds=['id=%s'], params=[id], df=FULL_DATE_FORMAT)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectUpdateHandler(BaseHandler):
    @coroutine
    def post(self):
        """
        @api {post} /api/project/update 更新项目
        @apiName ProjectUpdateHandler
        @apiGroup Project

        @apiParam {String} name 名称
        @apiParam {String} description 描述
        @apiParam {String} repos_name 仓库名字
        @apiParam {String} repos_url 仓库地址

        @apiUse Success
        """
        try:
            sets = ['name=%s', 'description=%s', 'repos_name=%s', 'repos_url=%s', 'mode=%s']
            conds = ['id=%s']
            params = [self.params['name'], self.params['description'], self.params['repos_name'], self.params['repos_url'], self.params['mode'],
                      self.params['id']]
            yield self.project_service.update(sets=sets, conds=conds, params=params)
            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectDeploymentHandler(BaseHandler):
    @coroutine
    def post(self):
        """
        @api {post} /api/project/deployment 部署镜像
        @apiName ProjectDeploymentHandler
        @apiGroup Project

        @apiParam {String} image_name 镜像名称
        @apiParam {String} public_ip 公共ip

        @apiUse Success
        """
        try:
            login_info = yield self.server_service.fetch_ssh_login_info(self.params)
            self.params.update(login_info)
            yield self.project_service.deployment(self.params)
            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectImageCreationHandler(BaseHandler):
    @coroutine
    def post(self):
        """
        @api {post} /api/project/image/creation 构建仓库镜像
        @apiName ProjectImageCreationHandler
        @apiGroup Project

        @apiParam {String} prj_name 项目名称
        @apiParam {String} repos_url 仓库地址
        @apiParam {String} branch_name 分支名字
        @apiParam {String} version 版本号

        @apiUse Success
        """
        try:
            login_info = yield self.server_service.fetch_ssh_login_info({'public_ip': settings['ip_for_image_creation']})
            self.params.update(login_info)
            yield self.project_service.create_image(self.params)
            arg = {'name': self.params['prj_name'], 'version': self.params['version']}
            yield self.project_versions_service.add(arg)
            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectVersionsHandler(BaseHandler):
    @coroutine
    def get(self):
        """
        @api {get} /api/project/versions 获取相关项目的所有版本
        @apiName ProjectVersionsHandler
        @apiGroup Project

        @apiParam {String} prj_name 项目名字
        @apiSuccessExample Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": []
            }
        """
        try:
            data = yield self.project_versions_service.select(fields='version', conds=['name=%s'], params=[self.get_argument('prj_name')], ct=False, ut=False)
            self.success([x['version'] for x in data])
        except:
            self.error()
            self.log.error(traceback.format_exc())

class ProjectImageFindHandler(BaseHandler):
    @coroutine
    def get(self):
        """
        @api {get} /api/project/image?prj_name=""  获取某一项目的所有镜像信息
        @apiName ProjectImageFindHandler
        @apiGroup Project

        @apiParam {String} prj_name 项目名称

        @apiSuccessExample Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {}
            }
        """
        try:
            self.params.update({"prj_name": self.get_argument('prj_name')})
            login_info = yield self.server_service.fetch_ssh_login_info({'public_ip': settings['ip_for_image_creation']})
            self.params.update(login_info)
            data, err = yield self.project_service.find_image(self.params)
            if err:
                self.error(err)
                return
            self.success(data)
        except:
            self.error()
            self.log.error(traceback.format_exc())

