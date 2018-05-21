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
                     SERVICE_STATUS, DEPLOYMENT_TYPE, K8S_SERVICE_TYPE


class K8sServiceYamlGenerateHandler(BaseHandler):
    @is_login
    def post(self):
        """
        @api {post} /api/service/generate 生成服务yaml配置
        @apiName K8sServiceYamlGenerateHandler
        @apiGroup Service

        @apiUse cidHeader

        @apiParam {String} service_name 服务名称
        @apiParam {String} app_name 应用名称
        @apiParam {Number} app_id 应用ID
        @apiParam {Number} service_source 服务来源（1.内部服务，2.外部服务）
        @apiParam {[]Number} deployment_ids 部署列表
        @apiParam {[]String} deployment_names 部署列表
        @apiParam {Number} service_type 服务类型（1.集群内访问，2.集群内外部可访问，3.负载均衡器）
        @apiParam {String} clusterIP 集群IP
        @apiParam {String} loadBalancerIP 负载均衡器IP
        @apiParam {[]String} externalIPs 外部IP
        @apiParam {[]{'name', 'protocol', 'port', 'targetPort', 'nodePort'}} ports 容器端口

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": "yaml"
            }
        """
        with catch(self):
            self.guarantee('app_id', 'app_name', 'service_name', 'service_source', 'service_type', 'deployment_ids',
                           'deployment_names')

            service_name = self.params['app_name'] + "." + self.params['service_name']

            yaml_json = {
                            'apiVersion': 'v1',
                            'kind': 'Service',
                            'metadata': {
                                'name': service_name,
                                'labels': {
                                    'internal_name': service_name,
                                    'app_id': str(self.params['app_id'])
                                }
                            },
                            'spec': {
                                'selector': {
                                    'matchLabels': {
                                        'app_id': str(self.params['app_id'])
                                    },
                                    'matchExpressions': [
                                        {'key': 'internal_name',
                                         'operator': 'In',
                                         'values': self.params['deployment_names']}
                                    ]
                                },
                                'type': K8S_SERVICE_TYPE[self.params['service_type']]
                            }
            }

            if self.params.get('ports'):
                yaml_json['spec']['ports'] = self.params['ports']

            if self.params.get('clusterIP'):
                yaml_json['spec']['clusterIP'] = self.params['clusterIP']

            if self.params.get('externalIPs'):
                yaml_json['spec']['externalIPs'] = self.params['externalIPs']

            result = yaml.dump(yaml_json, default_flow_style=False)
            self.success(result)


class K8sServiceHandler(WebSocketBaseHandler):
    def on_message(self, message):
        self.params.update(json.loads(message))

        try:
            args = ['app_id', 'app_name', 'service_name', 'deployment_ids', 'yaml']
            self.guarantee(*args)
            validate_k8s_object_name(self.params['deployment_name'])

            # 检查服务名称是否冲突
            deployment_info = self.deployment_service.sync_select({'id': self.params['deployment_ids'][0]}, one=True)
            server_id = deployment_info['server_id']
            duplicate = self.deployment_service.sync_select({'server_id': server_id, 'name': self.params['service_name']})
            if duplicate:
                raise ValueError('该集群内已有同名服务运行，请换用其他名称')

            # 获取需要部署的主机IP
            server_info = self.server_service.sync_select(conds={'id': server_id}, one=True)
            if not server_info:
                raise ValueError('没有可用于部署的主机，请尝试其他集群')

            # 记录用户操作应用开始构建的动作


            # 生成yaml文件并归档到服务器yaml目录下
            filename = self.save_yaml(self.params['app_name'], self.params['service_name'], 'service',
                                      self.params['yaml'])

            # 获取集群master的信息并进行部署
            login_info = self.application_service.sync_fetch_ssh_login_info({'public_ip': server_info['public_ip']})
            login_info.update({'filename': filename})
            out, err = self.k8s_apply(params=login_info, out_func=self.write_message)

            # 生成部署数据
            log = {"out": out, "err": err}
            arg = {'name': self.params['service_name'], 'app_id': self.params['app_id'],
                   'type': K8S_SERVICE_TYPE[int(self.params.get('type', K8S_SERVICE_TYPE.index('ClusterIP')))],
                   'state': SERVICE_STATUS['failure'] if err else SERVICE_STATUS['success'],
                   'yaml': self.params['yaml'], 'log': json.dumps(log)}
            arg.update(self.get_lord())
            self.service_service.sync_add(arg)

            if err:
                self.application_service.sync_update({'status': APPLICATION_STATE['abnormal']},
                                                     {'id': self.params.get('app_id')})
            else:
                self.application_service.sync_update({'status': APPLICATION_STATE['normal']},
                                                     {'id': self.params.get('app_id')})

            # 反馈结果
            self.write_message(FAILURE if err else SUCCESS)
        except Exception as e:
            self.log.error(traceback.format_exc())
            self.write_message(str(e))
            self.write_message(FAILURE)
        finally:
            self.close()