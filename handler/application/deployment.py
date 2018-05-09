import traceback
import json
import os
import yaml

from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from handler.base import BaseHandler, WebSocketBaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from utils.general import validate_application_name, validate_image_name, validate_deployment_name
from setting import settings
from handler.user import user
from constant import SUCCESS, FAILURE, OPERATION_OBJECT_STYPE, OPERATE_STATUS, LABEL_TYPE, PROJECT_OPERATE_STATUS, \
                     RIGHT, SERVICE, FORM_COMPANY, FORM_PERSON, MSG_PAGE_NUM, APPLICATION_STATE, DEPLOYMENT_STATUS, \
                     SERVICE_STATUS, DEPLOYMENT_TYPE


class K8sDeploymentHandler(WebSocketBaseHandler):
    def save_yaml(self, app_name, deployment_name, yaml):
        full_path = os.path.join('/var/www/Dashboard/static', 'yaml')
        if not os.path.exists(full_path): os.makedirs(full_path)

        filename = app_name + "_" + deployment_name + ".yaml"
        fullname = os.path.join(full_path, filename)

        with open(fullname, 'wb') as f:
            f.write(yaml.encode())

        return filename

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
        self.params = json.loads(message)

        try:
            args = ['app_id', 'app_name', 'deployment_name', 'server_id', 'yaml']
            self.guarantee(*args)
            validate_deployment_name(self.params['deployment_name'])

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
            filename = self.save_yaml(self.params['app_name'], self.params['deployment_name'], self.params['yaml'])

            # 获取集群master的信息并进行部署
            login_info = self.application_service.sync_fetch_ssh_login_info({'public_ip': server_info['public_ip']})
            login_info.update({'filename': filename})
            out, err = self.deployment_service.k8s_deploy(params=login_info, out_func=self.write_message)

            # 生成部署数据
            log = {"out": out, "err": err}
            arg = {'name': self.params['deployment_name'], 'app_id': self.params['app_id'], 'type': DEPLOYMENT_TYPE['k8s'],
                   'status': DEPLOYMENT_STATUS['fail'] if err else DEPLOYMENT_STATUS['complete'],
                   'yaml': self.params['yaml'], 'verbose': json.dumps(log), 'server_id': self.params['server_id']}
            arg.update(self.get_lord())
            self.deployment_service.add_deployment(arg)

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


class K8sDeploymentNameCheck(BaseHandler):
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
        self.guarantee('name', 'app_id')

        validate_deployment_name(self.params['name'])

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
        @apiParam {Number} replica_num 预期POD数量
        @apiParam {Dict} pod_label POD模板标签
        @apiParam {String} container_name 容器名称
        @apiParam {String} image_name 容器镜像名称
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

        self.guarantee('app_name', 'deployment_name', 'replica_num', 'container_name', 'image_name')

        deployment_name = self.params['app_name']+"-"+self.params['deployment_name']
        labels = {'app': deployment_name}

        # 如果用户配置了POD模板标签，则添加到YAML内容中
        if self.params.get('pod_label'):
            labels.update(self.params['pod_label'])

        yaml_json = {'apiVersion': 'apps/v1',
                     'kind': 'Deployment',
                     'metadata': {
                         'name': deployment_name
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
                                 'containers': [
                                     {
                                         'name': self.params['container_name'],
                                         'image': self.params['image_name']
                                     }
                                 ]
                             }
                         }
                     }
                     }

        if self.params.get('ports'):
            yaml_json['spec']['template']['spec']['containers'][0]['ports'] = self.params.get('ports')

        result = yaml.dump(yaml_json, default_flow_style=False)
        self.success(result)





