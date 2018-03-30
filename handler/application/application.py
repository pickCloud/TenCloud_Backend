

import traceback
import json

from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from handler.base import BaseHandler, WebSocketBaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from utils.general import validate_application_name
from setting import settings
from handler.user import user
from constant import SUCCESS, FAILURE, OPERATION_OBJECT_STYPE, OPERATE_STATUS,\
      RIGHT, SERVICE, FORM_COMPANY, FORM_PERSON, MSG_PAGE_NUM, APPLICATION_STATE, DEPLOYMENT_STATUS, SERVICE_STATUS


class ApplicationNewHandler(BaseHandler):
    @require(RIGHT['add_project'])
    @coroutine
    def post(self):
        """
        @api {post} /api/application/new 创建新应用
        @apiName ApplicationNewHandler
        @apiGroup Application

        @apiUse cidHeader

        @apiParam {String} name 应用名称
        @apiParam {String} description 描述
        @apiParam {String} repos_name 仓库名称
        @apiParam {String} repos_ssh_url 应用在github的ssh地址
        @apiParam {String} repos_https_url 应用在github的https地址
        @apiParam {String} logo_url LOGO的url地址
        @apiParam {Number} image_id 镜像ID

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "id": int,
                    "name": str,
                    "description": str
                }
            }
        """
        with catch(self):
            self.guarantee('name')
            self.log.info('Create new application, name: %s, repos name: %s, repos url: %s'
                          % (self.params.get('name'), self.params.get('repos_name'), self.params.get('repos_https_url')))

            # 检查应用名称是否合法
            validate_application_name(self.params.get('name'))

            # 检查是否有重复的应用
            param = self.get_lord()
            param['name'] = self.params.get('name')
            is_duplicate_name = yield self.application_service.select(param)
            if is_duplicate_name:
                self.log.error('Failed to create new application because of duplicate name %s' % param['name'])
                self.error('该应用名称已被使用，请换用其他名称')
                return

            # 添加应用信息和公司应用相关的数据权限
            self.params.update(self.get_lord())
            self.params.pop('token')
            new_app = yield self.application_service.add(self.params)

            if self.params.get('form') == FORM_COMPANY:
                param = {'uid': self.current_user['id'], 'cid': self.params.get('cid'), 'aid': new_app['id']}
                self.user_access_application_service.add(param)

            self.log.info('Succeeded to create new application, name: %s, repos name: %s, repos url: %s'
                          % (self.params.get('name'), self.params.get('repos_name'), self.params.get('repos_https_url')))
            self.success(new_app)


class ApplicationDeleteHandler(BaseHandler):
    @require(RIGHT['delete_project'], service=SERVICE['a'])
    @coroutine
    def post(self):
        """
        @api {post} /api/application/del 删除应用
        @apiName ApplicationDeleteHandler
        @apiGroup Application

        @apiUse cidHeader

        @apiParam {number[]} id 项目id

        @apiUse Success
        """
        with catch(self):
            self.log.info('Delete the application, ID: %s' % (self.params.get('id')))

            yield self.application_service.delete({'id': self.params.get('id')})
            self.log.info('Succeeded to delete the application, ID: %s' % (self.params.get('id')))

            self.success()


class ApplicationInfoHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/application 应用信息
        @apiName ApplicationInfoHandler
        @apiGroup Application

        @apiUse cidHeader

        @apiParam {Number} id 应用ID
        @apiParam {Number} status 应用状态(0.初创建 1.正常 2.异常)
        @apiParam {Number} page 页数
        @apiParam {Number} page_num 每页显示项数
        @apiParam {String} label 应用标签

        @apiDescription 样例: /api/application?id=\d&status=\d&page=\d&page_num=\d&label=\w*

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": int,
                        "name": str,
                        "description": str,
                        ...
                    },
                    ...
                ]
            }
        """
        with catch(self):
            # 获取应用信息，如果未填写id的话则获取所有满足条件的应用
            self.params.update(self.get_lord())
            self.params.pop('token')
            app_info = yield self.application_service.select(self.params)
            app_info = yield self.filter(app_info, service=SERVICE['a'])

            # 对结果进行分页显示
            page = int(self.params.pop('page', 1))
            page_num = int(self.params.pop('page_num', MSG_PAGE_NUM))
            self.success(app_info[page_num * (page - 1):page_num * page])


class ApplicationBriefHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/application/brief 应用概述信息
        @apiName ApplicationBriefHandler
        @apiGroup Application

        @apiUse cidHeader

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "app_num": 1,
                    "deploy_num": 2,
                    "pods_num": 0,
                    "docker_num": 0,
                    "service_num": 1
                }
            }
        """
        with catch(self):
            param = self.get_lord()
            param['status'] = APPLICATION_STATE['normal']
            app_list = yield self.application_service.select(conds=param)

            param['status'] = DEPLOYMENT_STATUS['complete']
            deploy_list = yield self.deployment_service.select(conds=param)

            param['status'] = SERVICE_STATUS['success']
            service_list = yield self.service_service.select(conds=param)

            self.success({
                'app_num': len(app_list),
                'deploy_num': len(deploy_list),
                'pods_num': 0,
                'docker_num': 0,
                'service_num': len(service_list)
            })
