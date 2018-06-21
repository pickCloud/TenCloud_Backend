import traceback
import json
import os
import yaml

from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from handler.base import BaseHandler, WebSocketBaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from utils.general import validate_application_name, validate_image_name, validate_k8s_object_name
from setting import settings
from handler.user import user
from constant import SUCCESS, FAILURE, OPERATION_OBJECT_STYPE, OPERATE_STATUS, LABEL_TYPE, PROJECT_OPERATE_STATUS, \
                     RIGHT, SERVICE, FORM_COMPANY, FORM_PERSON, MSG_PAGE_NUM, APPLICATION_STATE, DEPLOYMENT_STATUS, \
                     SERVICE_STATUS, DEPLOYMENT_TYPE


class K8sDeploymentHandler(WebSocketBaseHandler):


    @coroutine
    def init_operation_log(self, log_params):
        yield self.server_operation_service.add(params={
            'user_id': log_params['user_id'],
            'object_id': log_params['object_id'],
            'object_type': log_params['object_type'],
            'operation': PROJECT_OPERATE_STATUS['deploy'],
            'operation_status': OPERATE_STATUS['processing'],
        })

    def on_message(self, message):
        self.params.update(json.loads(message))

        try:
            args = ['app_id', 'app_name', 'deployment_name', 'server_id', 'yaml']
            self.guarantee(*args)
            validate_k8s_object_name(self.params['deployment_name'])

            # 检查部署名称是否冲突
            duplicate = self.deployment_service.sync_select({'server_id': self.params['server_id'], 'name': self.params['deployment_name']})
            if duplicate:
                raise ValueError('该部署名称已被使用，请换用其他名称')

            # 获取需要部署的主机IP
            server_info = self.server_service.sync_select(conds={'id': self.params['server_id']}, one=True)
            if not server_info:
                raise ValueError('没有可用于部署的主机，请尝试其他集群')

            # 记录用户操作应用开始构建的动作
            log_params = {
                'user_id': self.current_user['id'],
                'object_id': self.params['app_id'],
                'object_type': OPERATION_OBJECT_STYPE['deployment'],
            }
            IOLoop.current().spawn_callback(callback=self.init_operation_log, params=log_params)

            # 生成yaml文件并归档到服务器yaml目录下
            filename = self.save_yaml(self.params['app_name'], self.params['deployment_name'], 'deployment', self.params['yaml'])

            # 获取集群master的信息并进行部署
            login_info = self.application_service.sync_fetch_ssh_login_info({'public_ip': server_info['public_ip']})
            login_info.update({'filename': filename})
            out, err = self.k8s_apply(params=login_info, out_func=self.write_message)

            # 生成部署数据
            log = {"out": out, "err": err}
            arg = {'name': self.params['deployment_name'], 'app_id': self.params['app_id'], 'type': DEPLOYMENT_TYPE['k8s'],
                   'status': DEPLOYMENT_STATUS['fail'] if err else DEPLOYMENT_STATUS['complete'],
                   'yaml': self.params['yaml'], 'log': json.dumps(log), 'server_id': self.params['server_id']}
            arg.update(self.get_lord())
            res = self.deployment_service.add_deployment(arg)
            self.write_message('deployment ID:' + str(res.get('id', 0)))

            if err:
                self.application_service.sync_update({'status': APPLICATION_STATE['abnormal']}, {'id': self.params.get('app_id')})
            else:
                self.application_service.sync_update({'status': APPLICATION_STATE['normal']}, {'id': self.params.get('app_id')})

            # 反馈结果
            self.write_message(FAILURE if err else SUCCESS)

        except Exception as e:
            self.log.error(traceback.format_exc())
            self.write_message(str(e))
            self.write_message(FAILURE)
        finally:
            self.close()


class K8sDeploymentNameCheckHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/deployment/check_name 检查部署名称
        @apiName K8sDeploymentNameCheck
        @apiGroup Deployment

        @apiUse cidHeader

        @apiParam {String} name 公司名称
        @apiParam {Number} app_id 应用ID
        @apiParam {Number} server_id 服务器ID

        @apiUse Success
        """
        with catch(self):
            self.guarantee('name', 'app_id')

            validate_k8s_object_name(self.params['name'])

            is_duplicate = yield self.deployment_service.select({'name': self.params['name'],
                                                                 'app_id': self.params['app_id']})
            if is_duplicate:
                self.error('该部署名称已被使用，请换用其他名称')
                return

            if self.params.get('server_id'):
                is_duplicate = yield self.deployment_service.select({'name': self.params['name'],
                                                                     'server_id': self.params['server_id']})
                if is_duplicate:
                    self.error('该部署名称已被使用，请换用其他名称或在其他集群上部署')
                    return

            self.success()


class K8sDeploymentYamlGenerateHandler(BaseHandler):
    @is_login
    def post(self):
        """
        @api {post} /api/deployment/generate 生成部署yaml配置文件
        @apiName K8sDeploymentYamlGenerateHandler
        @apiGroup Deployment

        @apiUse cidHeader

        @apiParam {String} deployment_name 部署名称
        @apiParam {Number} app_id 应用ID
        @apiParam {String} app_name 应用名称
        @apiParam {Number} replica_num 预期POD数量
        @apiParam {Dict} pod_label POD模板标签
        @apiParam {[]{'name','image','ports'}} containers 容器
        @apiParam {String} name 容器名称
        @apiParam {String} image 容器镜像名称
        @apiParam {[]{'protocol','containerPort','name'}} ports 容器端口

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": "yaml"
            }
        """

        # apiVersion: apps/v1
        # kind: Deployment
        # metadata:
        #   name: nginx-deployment
        # spec:
        #   replicas: 3
        #   selector:
        #     matchLabels:
        #       app: nginx
        #   template:
        #     metadata:
        #       labels:
        #         app: nginx
        #     spec:
        #       containers:
        #       - name: nginx
        #         image: nginx:1.7.9
        #         ports:
        #         - containerPort: 80
        #           protocol: TCP
        #           name: port1
        with catch(self):
            self.guarantee('app_id', 'app_name', 'deployment_name', 'replica_num', 'containers')

            deployment_name = self.params['app_name']+"."+self.params['deployment_name']
            labels = {'internal_name': deployment_name, 'app_id': str(self.params['app_id'])}

            # 如果用户配置了POD模板标签，则添加到YAML内容中
            if self.params.get('pod_label'):
                labels.update(self.params['pod_label'])

            yaml_json = {'apiVersion': 'apps/v1',
                         'kind': 'Deployment',
                         'metadata': {
                             'name': deployment_name,
                             'labels': labels
                         },
                         'spec': {
                             'replicas': self.params['replica_num'],
                             'selector': {
                                 'matchLabels': labels,
                             },
                             'template': {
                                 'metadata': {
                                     'labels': labels,
                                 },
                                 'spec': {
                                     'containers': []
                                 }
                             }
                         }
                         }

            if self.params.get('containers'):
                yaml_json['spec']['template']['spec']['containers'] = self.params.get('containers')

            result = yaml.dump(yaml_json, default_flow_style=False)
            self.success(result)


class DeploymentBriefHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/deployment/brief 部署列表
        @apiName DeploymentBriefHandler
        @apiGroup Deployment

        @apiUse cidHeader

        @apiParam {Number} [app_id] 应用ID
        @apiParam {Number} [status] 部署状态(1.进行中, 2.已完成, 3.失败)
        @apiParam {Number} [deployment_id] 部署ID
        @apiParam {Number} [show_yaml] 是否查询yaml内容(0.否 1.是)
        @apiParam {Number} [show_log] 是否查询Log内容(0.否 1.是)
        @apiParam {Number} [page] 页数
        @apiParam {Number} [page_num] 每页显示项数

        @apiDescription 样例: /api/deployment/brief?app_id=\d&status=\d&page=\d&page_num=\d
                        or /api/deployment/brief?deployment_id=\d&

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": int,
                        "name": str,
                        "status": int,
                        ...
                    },
                    ...
                ]
            }
        """
        with catch(self):
            param = self.get_lord()

            if self.params.get('app_id'):
                param['app_id'] = int(self.params.get('app_id'))
            if self.params.get('status'):
                param['status'] = int(self.params.get('status'))
            if self.params.get('deployment_id'):
                param['id'] = int(self.params.get('deployment_id'))
            page = int(self.params.get('page', 1))
            page_num = int(self.params.get('page_num', MSG_PAGE_NUM))
            show_yaml = int(self.params.get('show_yaml', 0))
            show_log = int(self.params.get('show_log', 0))

            brief = yield self.deployment_service.select(conds=param)

            for i in brief:
                app_info = yield self.application_service.select(conds={'id': i['app_id']}, one=True)
                i['app_name'] = app_info['name']

                # 从k8s集群上报过来的yaml信息中解析出pod状态等信息
                verbose = i.pop('verbose', None)
                verbose = yaml.load(verbose) if verbose else None
                if verbose:
                    i['replicas'] = verbose['status'].get('replicas', 0)
                    i['readyReplicas'] = verbose['status'].get('readyReplicas', 0)
                    i['updatedReplicas'] = verbose['status'].get('updatedReplicas', 0)
                    i['availableReplicas'] = verbose['status'].get('availableReplicas', 0)

                # 去除一些查询列表时用不到的字段
                if not show_log: i.pop('log', None)
                if not show_yaml: i.pop('yaml', None)

            self.success(brief[page_num*(page-1):page_num*page])


class DeploymentLastestHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/deployment/latest 最新的部署
        @apiName DeploymentLastestHandler
        @apiGroup Deployment

        @apiUse cidHeader

        @apiParam {Number} app_id 应用ID
        @apiParam {Number} [show_yaml] 是否查询yaml内容(0.否 1.是)
        @apiParam {Number} [show_log] 是否查询Log内容(0.否 1.是)

        @apiDescription 获取最新的部署对象

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "id": int,
                    "name": str,
                    "status": int,              //部署状态(1.进行中, 2.已完成, 3.失败)
                    "app_id": int,
                    "app_name": str,
                    "type": int,                //部署类型(1 K8S部署, 2 Docker原生部署)
                    "server_id": int,
                    "replicas": int,            //预设实例数量
                    "readyReplicas": int,       //当前实例数量
                    "updatedReplicas": int,     //更新实例数量
                    "availableReplicas": int,   //可用实例数量
                    "form": int,
                    "lord": int,
                    "create_time": str,
                    "update_time": str,
                }
            }
        """
        with catch(self):
            param = self.get_lord()

            if self.params.get('app_id'):
                param['app_id'] = int(self.params.get('app_id'))

            show_yaml = int(self.params.get('show_yaml', 0))
            show_log = int(self.params.get('show_log', 0))

            deployment_info = yield self.deployment_service.select(conds=param, one=True, extra=' ORDER BY update_time DESC ')
            if not deployment_info:
                self.success()
                return

            app_info = yield self.application_service.select(conds={'id': deployment_info['app_id']}, one=True)
            deployment_info['app_name'] = app_info['name']

            # 从k8s集群上报过来的yaml信息中解析出pod状态等信息
            verbose = deployment_info.pop('verbose', None)
            verbose = yaml.load(verbose) if verbose else None
            if verbose:
                deployment_info['replicas'] = verbose['status'].get('replicas', 0)
                deployment_info['readyReplicas'] = verbose['status'].get('readyReplicas', 0)
                deployment_info['updatedReplicas'] = verbose['status'].get('updatedReplicas', 0)
                deployment_info['availableReplicas'] = verbose['status'].get('availableReplicas', 0)

            # 去除一些查询列表时用不到的字段
            if not show_log: deployment_info.pop('log', None)
            if not show_yaml: deployment_info.pop('yaml', None)

            self.success(deployment_info)

class DeploymentReplicasSetSourceHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/deployment/replicas 部署的ReplicasSet信息
        @apiName DeploymentReplicasSetSourceHandler
        @apiGroup Deployment

        @apiUse cidHeader

        @apiParam {Number} deployment_id 部署ID
        @apiParam {Number} show_verbose 显示具体yaml内容

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": int,
                        "name": str,
                        "deployment_id": str,
                        "replicas": int,        //预设pod数量
                        "availableReplicas": int,   //当前pod数量
                        "readyReplicas": int,       //就绪pod数量
                        "verbose": str,
                        "create_time": time,
                        "update_time": time
                    },
                    ...
                ]
            }
        """
        with catch(self):
            self.guarantee('deployment_id')
            show_yaml = int(self.params.get('show_yaml', 0))

            replicaset = yield self.replicaset_service.select({'deployment_id': self.params['deployment_id']})
            for i in replicaset:
                verbose = i.get('verbose', None) if show_yaml else i.pop('verbose', None)
                if verbose:
                    verbose = yaml.load(verbose)
                    i['replicas'] = verbose['status'].get('replicas', None)
                    i['availableReplicas'] = verbose['status'].get('availableReplicas', None)
                    i['readyReplicas'] = verbose['status'].get('readyReplicas', None)

            self.success(replicaset)


class DeploymentPodSourceHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/deployment/pods 部署的Pod信息
        @apiName DeploymentPodSourceHandler
        @apiGroup Deployment

        @apiUse cidHeader

        @apiParam {Number} deployment_id 部署ID
        @apiParam {Number} show_verbose 显示具体yaml内容

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": int,
                        "name": str,
                        "deployment_id": str,
                        "readyStatus": str,        //就绪情况
                        "podStatus": str,           //pod状态
                        "restartStatus": int,       //重启次数
                        "labels": [],               //标签
                        "verbose": str,
                        "create_time": time,
                        "update_time": time
                    },
                    ...
                ]
            }
        """
        with catch(self):
            self.guarantee('deployment_id')
            show_yaml = int(self.params.get('show_yaml', 0))

            pods = yield self.pod_service.select({'deployment_id': self.params['deployment_id']})
            for i in pods:
                verbose = i.get('verbose', None) if show_yaml else i.pop('verbose', None)
                if verbose:
                    verbose = yaml.load(verbose)

                    ready = 0
                    total = 0
                    restart = 0
                    for container in verbose['status'].get('containerStatuses', []):
                        ready += 1 if container.get('ready', False) else 0
                        total += 1
                        restart += int(container.get('restartCount', 0))

                    i['readyStatus'] = str(ready) + '/' + str(total)
                    i['podStatus'] = verbose['status'].get('phase', '')
                    i['restartStatus'] = restart
                    i['labels'] = verbose['metadata'].get('labels', [])

            self.success(pods)