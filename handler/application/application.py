

import traceback
import json
import os

from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from handler.base import BaseHandler, WebSocketBaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from utils.general import validate_application_name
from setting import settings
from handler.user import user
from constant import SUCCESS, FAILURE, OPERATION_OBJECT_STYPE, OPERATE_STATUS, LABEL_TYPE, PROJECT_OPERATE_STATUS, \
                     RIGHT, SERVICE, FORM_COMPANY, FORM_PERSON, MSG_PAGE_NUM, APPLICATION_STATE, DEPLOYMENT_STATUS, \
                     SERVICE_STATUS, IMAGE_STATUS


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
        @apiParam {[]Number} labels 标签ID(传递时注意保证ID是从小到大的顺序)

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

            # 添加应用信息，标签关系和公司应用相关的数据权限
            param.update(self.params)
            param.pop('token', None)
            param.pop('cid', None)
            param['labels'] = ','.join(str(i) for i in param.pop('labels', []))
            param['logo_url'] = settings['qiniu_header_bucket_url'] + param['logo_url'] \
                                if self.params.get('logo_url', None) else ''
            new_app = yield self.application_service.add(param)

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


class ApplicationUpdateHandler(BaseHandler):
    @require(RIGHT['modify_project_info'], service=SERVICE['a'])
    @coroutine
    def post(self):
        """
        @api {post} /api/application/update 更新应用
        @apiName ApplicationUpdateHandler
        @apiGroup Application

        @apiUse cidHeader

        @apiParam {Number} id 项目id
        @apiParam {String} name 应用名称
        @apiParam {String} description 描述
        @apiParam {String} repos_name 仓库名称
        @apiParam {String} repos_ssh_url 应用在github的ssh地址
        @apiParam {String} repos_https_url 应用在github的https地址
        @apiParam {String} logo_url LOGO的url地址
        @apiParam {[]Number} labels 标签ID(传递时注意保证ID是从小到大的顺序)

        @apiUse Success
        """
        with catch(self):
            self.log.info('Update the application, ID: %s' % (self.params.get('id')))

            # 检查修改后名字是否会出现冲突
            param = self.get_lord()
            param['name'] = self.params.get('name')
            app_info = yield self.application_service.select(param, one=True)
            if app_info and app_info['id'] != self.params.get('id'):
                self.log.info('Failed to update application[%s] because of duplicate name' % (self.params.get('id')))
                self.error('该应用名称已被使用，请换用其他名称')
                return

            # 无冲突项，则更新应用信息
            sets = {
                'name': self.params.get('name'),
                'description': self.params.get('description'),
                'repos_name': self.params.get('repos_name'),
                'repos_ssh_url': self.params.get('repos_ssh_url'),
                'repos_https_url': self.params.get('repos_https_url'),
                'labels': ','.join(str(i) for i in self.params.pop('labels', []))
            }
            if self.params.get('logo_url', ''):
                sets['logo_url'] = self.params.get('logo_url') \
                                   if self.params.get('logo_url').startswith(settings['qiniu_header_bucket_url']) \
                                   else settings['qiniu_header_bucket_url'] + self.params.get('logo_url')
            yield self.application_service.update(sets=sets, conds={'id': self.params.get('id')})

            self.log.info('Succeed in updating the application, ID: %s' % (self.params.get('id')))
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
        @apiParam {Number} label 应用标签ID

        @apiDescription 样例: /api/application?id=\d&status=\d&page=\d&page_num=\d&label=\d

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
            param = self.params
            param.update(self.get_lord())
            param.pop('token', None)
            param.pop('cid', None)
            page = int(param.pop('page', 1))
            page_num = int(param.pop('page_num', MSG_PAGE_NUM))
            label = int(param.pop('label', 0))

            # 获取应用信息，如果未填写id的话则获取所有满足条件的应用
            app_info = yield self.application_service.fetch_with_label(param, label)
            app_info = yield self.filter(app_info, service=SERVICE['a'])

            # 对结果进行分页显示
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


class ImageCreationHandler(WebSocketBaseHandler):
    def on_message(self, message):
        self.params = json.loads(message)

        try:
            args = ['image_name', 'version', 'repos_https_url', 'branch_name', 'app_id', 'app_name', 'dockerfile']

            self.guarantee(*args)

            # 记录用户操作应用开始构建的动作
            log_params = {
                'user_id': self.current_user['id'],
                'object_id': self.params['app_id'],
                'object_type': OPERATION_OBJECT_STYPE['application'],
            }
            IOLoop.current().spawn_callback(callback=self.init_operation_log, params=log_params)

            # 生成dockerfile文件
            self.save_dockerfile(self.params['image_name'], self.params['app_name'], self.params['dockerfile'])
            # 获取构建服务器的信息并进行构建
            login_info = self.application_service.sync_fetch_ssh_login_info({'public_ip': settings['ip_for_image_creation']})
            self.params.update(login_info)
            out, err = self.application_service.create_image(params=self.params, out_func=self.write_message)

            # 生成镜像数据
            log = {"out": out, "err": err}
            arg = {'name': self.params['image_name'], 'version': self.params['version'], 'app_id': self.params['app_id'],
                   'dockerfile': self.params['dockerfile'], 'log': json.dumps(log)}
            arg.update(self.get_lord())
            self.application_service.add_image_data(arg)

            # 构建成功或失败错误，刷新应用的状态（正常或异常）
            if err:
                self.application_service.sync_update({'status': APPLICATION_STATE['abnormal']}, {'id': self.params.get('app_id')})
                self.image_service.sync_update({'state': IMAGE_STATUS['failure']}, {'name': self.params['image_name'], 'version': self.params['version']})
            else:
                IOLoop.current().spawn_callback(callback=self.finish_operation_log, params=log_params)
                self.application_service.sync_update({'status': APPLICATION_STATE['normal']}, {'id': self.params.get('app_id')})
                self.image_service.sync_update({'state': IMAGE_STATUS['success']}, {'name': self.params['image_name'], 'version': self.params['version']})

            self.write_message(FAILURE if err else SUCCESS)
        except Exception as e:
            self.log.error(traceback.format_exc())
            self.write_message(FAILURE)
        finally:
            self.close()

    @coroutine
    def init_operation_log(self, log_params):
        yield self.server_operation_service.add(params={
            'user_id': log_params['user_id'],
            'object_id': log_params['object_id'],
            'object_type': log_params['object_type'],
            'operation': PROJECT_OPERATE_STATUS['build'],
            'operation_status': OPERATE_STATUS['fail'],
        })

    @coroutine
    def finish_operation_log(self, log_params):
        yield self.server_operation_service.update(
            sets={'operation_status': OPERATE_STATUS['success']},
            conds={
                'user_id': log_params['user_id'],
                'object_id': log_params['object_id'],
                'object_type': log_params['object_type']
            }
        )

    def save_dockerfile(self, image_name, app_name, dockerfile=''):
        if not dockerfile:
            raise ValueError('请输入Dockerfile内容')

        full_path = os.path.join(os.environ['HOME'], 'dockerfile')
        if not os.path.exists(full_path): os.makedirs(full_path)

        filename = os.path.join(full_path, app_name+"_"+image_name)

        with open(filename, 'wb') as f:
            f.write(dockerfile.encode())

        return image_name


class ImageUploadDockerfileHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/image/new 创建新应用
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
        @apiParam {[]Number} labels 标签ID(传递时注意保证ID是从小到大的顺序)

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
        pass