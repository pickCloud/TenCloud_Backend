__author__ = 'Jon'

import traceback
import json

from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from handler.base import BaseHandler, WebSocketBaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from setting import settings
from handler.user import user
from constant import PROJECT_STATUS, SUCCESS, FAILURE, OPERATION_OBJECT_STYPE, PROJECT_OPERATE_STATUS, OPERATE_STATUS,\
      RIGHT, SERVICE


class ProjectHandler(BaseHandler):
    @is_login
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
        with catch(self):
            result = yield self.project_service.fetch({'uid': self.current_user['id'], 'cid': self.params.get('cid')})

            self.success(result)


class ProjectNewHandler(BaseHandler):
    @require(RIGHT['add_project'])
    @coroutine
    def post(self):
        """
        @api {post} /api/project/new 创建新项目
        @apiName ProjectNewHandler
        @apiGroup Project

        @apiUse apiHeader

        @apiParam {String} name 名称
        @apiParam {String} image_name 镜像名字 (必需小写字母，分隔符可选)
        @apiParam {String} description 描述
        @apiParam {String} repos_name 仓库名称
        @apiParam {String} repos_url 仓库url
        @apiParam {String} http_url 项目在github的http地址
        @apiParam {Number} mode 类型
        @apiParam {Number} image_source 镜像来源
        @apiParam {String} version 用于导入镜像或下载镜像的版本

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
        with catch(self):
            if self.params.get('repos_url'):
                is_duplicate_url = yield self.project_service.select(conds={'repos_url': self.params['repos_url']}, one=True)

                if is_duplicate_url:
                    self.error('你选择的代码仓库，已有项目存在，项目名称【{prj_name}】'.format(prj_name=is_duplicate_url['name']))
                    return

            if self.params.get('image_source') and self.params.get('version'):
                version = self.params.pop('version')
                arg = {'name': self.params['name'], 'version': version, 'log': ''}
                yield self.project_service.insert_log(arg)

            result = yield self.project_service.add(params=self.params)

            yield self.server_operation_service.add(params={
                'user_id': self.current_user['id'],
                'object_id': result['id'],
                'object_type': OPERATION_OBJECT_STYPE['project'],
                'operation': PROJECT_OPERATE_STATUS['create'],
                'operation_status': OPERATE_STATUS['success'],
            })
            self.success(result)


class ProjectDelHandler(BaseHandler):
    @require(RIGHT['delete_project'], service=SERVICE['p'])
    @coroutine
    def post(self):
        """
        @api {post} /api/project/del 项目删除
        @apiName ProjectDelHandler
        @apiGroup Project

        @apiUse apiHeader

        @apiParam {number[]} id 项目id

        @apiUse Success
        """
        with catch(self):
            ids = self.params['id']
            yield self.project_service.delete({'id': ids})

            self.success()


class ProjectDetailHandler(BaseHandler):
    @is_login
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
                    "http_url": str,
                    "image_name": str,
                    "id": 2,
                    "name": str,
                    "create_time": str,
                    "update_time": str,
                    "status": str,
                    "mode": str,
                    "deploy_ips": str,
                }
                    ...
                ]
            }
        """
        with catch(self):
            result = yield self.project_service.fetch({'uid': self.current_user['id'], 'cid': self.params.get('cid'), 'pid': id})

            self.success(result)


class ProjectUpdateHandler(BaseHandler):
    @require(RIGHT['modify_project_info'], service=SERVICE['p'])
    @coroutine
    def post(self):
        """
        @api {post} /api/project/update 更新项目
        @apiName ProjectUpdateHandler
        @apiGroup Project

        @apiUse apiHeader

        @apiParam {String} id 项目id
        @apiParam {String} name 名称
        @apiParam {String} description 描述
        @apiParam {String} repos_name 仓库名字
        @apiParam {String} repos_url 仓库地址
        @apiParam {String} http_url 项目在github的仓库地址
        @apiParam {String} image_name 镜像名字
        @apiParam {String} mode 项目类型

        @apiUse Success
        """
        with catch(self):
            data = yield self.server_operation_service.add(params={
                'user_id': self.current_user['id'],
                'object_id': self.params['id'],
                'object_type': OPERATION_OBJECT_STYPE['project'],
                'operation': PROJECT_OPERATE_STATUS['change'],
                'operation_status': OPERATE_STATUS['fail'],
            })

            params = [
                    self.params['name'],
                    self.params['description'],
                    self.params['repos_name'],
                    self.params['repos_url'],
                    self.params['http_url'],
                    self.params['mode'],
                    self.params['image_name'],
                    self.params['id']
                    ]
            sets = {
                'name': self.params['name'],
                'description': self.params['description'],
                'repos_name': self.params['repos_name'],
                'repos_url': self.params['repos_url'],
                'http_url': self.params['http_url'],
                'mode': self.params['mode'],
                'image_name': self.params['image_name']
            }
            conds = {'id': self.params['id']}

            yield self.project_service.update(sets=sets, conds=conds)

            yield self.server_operation_service.update(
                    sets={'operation_status': OPERATE_STATUS['success']},
                    conds={'id': data['id']}
            )
            self.success()


class ProjectDeploymentHandler(WebSocketBaseHandler):

    def on_message(self, message):
        self.params = json.loads(message)
        try:
            args = ['image_name', 'container_name', 'ips', 'project_id']

            self.guarantee(*args)

            log_params = {
                    'user_id': self.current_user['id'],
                    'object_id': self.params['project_id'],
                    'object_type': OPERATION_OBJECT_STYPE['project'],
            }
            IOLoop.current().spawn_callback(self.init_operation_log, log_params)

            params = {'id': self.params['project_id'], 'status': PROJECT_STATUS['deploying']}
            self.project_service.sync_update_status(params)

            self.params["infos"] = []
            for ip in self.params['ips']:
                login_info = self.project_service.sync_fetch_ssh_login_info(ip)
                self.params['infos'].append(login_info)

            log = self.project_service.deployment(self.params, self.write_message)

            status, result = PROJECT_STATUS['deploy-success'], SUCCESS

            if log['has_err']:
                status, result = PROJECT_STATUS['deploy-failure'], FAILURE

            arg = [json.dumps(self.params['ips']), self.params['container_name'], status, self.params['project_id']]
            self.project_service.set_deploy_ips(arg)

            IOLoop.current().spawn_callback(self.finish_operation_log, log_params)

            self.write_message('ok')
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
            'operation': PROJECT_OPERATE_STATUS['deploy'],
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

class ProjectContainersListHanler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/project/containers/list 项目容器列表
        @apiName ProjectContainersList
        @apiGroup Project

        @apiParam {String} container_list 容器列表
        @apiParam {String} container_name 容器名字

        @apiSuccessExample {json} Success-Response
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    [
                        "1a050e4d7e43", # container id
                         "harbor-jobservice", # container name
                        "Up 3 weeks", # status
                        "2017-05-18 14:06:50" # created_time
                        "server_id" # server_id
                    ],
                    ...
                ]
            }
        """
        with catch(self):
            data = []
            for ip in json.loads(self.params['container_list']):
                server_id = yield self.server_service.fetch_server_id(ip['public_ip'])
                login_info = yield self.server_service.fetch_ssh_login_info(ip)
                ip.update(login_info)
                ip.update({'container_name': self.params['container_name']})
                info = yield self.project_service.list_containers(ip)
                if not info:
                    continue
                one_ip = []
                for i in info:
                    i[3] = i[3].split('+')[0].strip()
                    i.append(server_id)
                    one_ip.extend(i)
                data.append(one_ip)
            self.success(data)


class ProjectImageCreationHandler(WebSocketBaseHandler):

    def on_message(self, message):
        self.params = json.loads(message)

        try:
            args = ['prj_name', 'repos_url', 'branch_name', 'version', 'image_name', 'project_id']

            self.guarantee(*args)

            log_params = {
                'user_id': self.current_user['id'],
                'object_id': self.params['project_id'],
                'object_type': OPERATION_OBJECT_STYPE['project'],
            }
            IOLoop.current().spawn_callback(callback=self.init_operation_log, params=log_params)

            params = {'status': PROJECT_STATUS['building'], 'name': self.params['prj_name']}
            self.project_service.sync_update_status(params)

            login_info = self.project_service.sync_fetch_ssh_login_info({'public_ip': settings['ip_for_image_creation']})
            self.params.update(login_info)
            out, err = self.project_service.create_image(params=self.params, out_func=self.write_message)

            log = {"out": out, "err": err}
            arg = {'name': self.params['prj_name'], 'version': self.params['version'], 'log': json.dumps(log)}
            self.project_service.sync_insert_log(arg)

            params['status'], result = PROJECT_STATUS['build-success'], SUCCESS
            if err:
                params['status'], result = PROJECT_STATUS['build-failure'], FAILURE

            self.project_service.sync_update_status(params)
            IOLoop.current().spawn_callback(callback=self.finish_operation_log, params=log_params)
            self.write_message(result)
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

class ProjectImageLogHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, prj_name, version):
        """
        @api {get} /api/project/([\w\W]+)/image/([\w\W]+)/log 获取相关项目的某一版本的构建日志
        @apiName ProjectImageLogHandler
        @apiGroup Project

        @apiParam {String} prj_name 项目名字
        @apiParam {String} version 版本

        @apiSuccessExample Success-Response:
            HTTP/1.1 200 OK
            {
                "status":0,
                "msg": "success",
                "data": {
                    "log": {
                        "err": String[],
                        "out": String[],
                    }
                    "update_time": String,
                }
            }
        """
        with catch(self):
            out = yield self.project_versions_service.select(fields='log', conds={'name': prj_name, 'version': version},
                                                             ct=False, one=True)
            data = {"log": json.loads(out['log']), "update_time": out['update_time']}
            self.success(data)

    @require(RIGHT['delete_project_version'])
    @coroutine
    def delete(self, prj_name, version):
        """
       @api {delete} /api/project/([\w\W]+)/image/([\w\W]+)/log 删除相关项目的某一版本的构建日志
       @apiName ProjectImageLogHandler
       @apiGroup Project

       @apiUse apiHeader

       @apiParam {String} prj_name 项目名字
       @apiParam {String} version 版本

       @apiUse Success
       """
        with catch(self):
            data_id = yield self.project_service.select(fields='id',conds={'name': prj_name}, ct=False, ut=False, one=True)
            data = yield self.server_operation_service.add(params={
                'user_id': self.current_user['id'],
                'object_id': data_id['id'],
                'object_type': OPERATION_OBJECT_STYPE['project'],
                'operation': PROJECT_OPERATE_STATUS['delete_log'],
                'operation_status': OPERATE_STATUS['fail'],
            })

            yield self.project_versions_service.delete({'name': prj_name, 'version': version})

            yield self.server_operation_service.update(
                    sets={'operation_status': OPERATE_STATUS['success']},
                    conds={'id': data['id']}
            )
            self.success()


class ProjectVersionsHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, prj_name):
        """
        @api {get} /api/project/([\w\W]+)/versions 获取相关项目的所有版本
        @apiName ProjectVersionsHandler
        @apiGroup Project

        @apiParam {String} prj_name 项目名字
        @apiSuccessExample Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"id": int, "version": str, "update_time": str},
                    ...
                ]
            }
        """
        with catch(self):
            data = yield self.project_versions_service.version_list(prj_name)
            self.success(data)


class ProjectImageFindHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, prj_name):
        """
        @api {get} /api/project/([\w\W]+)/image 获取某一项目的所有镜像信息
        @apiName ProjectImageFindHandler
        @apiGroup Project

        @apiParam {String} prj_name 项目名称

        @apiSuccessExample Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    ["{Tag}", "{CreatedAt}"],
                    ...
                ]
            }
        """
        with catch(self):
            self.params.update({"prj_name": prj_name})
            login_info = yield self.server_service.fetch_ssh_login_info({'public_ip': settings['ip_for_image_creation']})
            self.params.update(login_info)
            data, err = yield self.project_service.find_image(self.params)
            if err:
                self.error(err)
                return
            self.success(data)


class ProjectImageUpload(user.FileUploadMixin):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/project/image/upload 镜像上传
        @apiName ProjectImageUpload
        @apiGroup Project


        @apiUse Success
        """
        with catch(self):
            filename = yield self.handle_file_upload()
            yield self.project_service.upload_image(filename)
            self.success()


class ProjectImageCloudDownload(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/project/image/cloud/download 云端下载导入
        @apiName ProjectImageDownload
        @apiGroup Project

        @apiParam {String} image_url 镜像下载地址

        @apiUse Success
        """
        with catch(self):
            yield self.project_service.cloud_download(self.params['image_url'])
            yield self.project_service.upload_image(self.params['image_url'].split('\\')[-1])
            self.success()