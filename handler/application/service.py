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
        @apiParam {Number} service_source 服务来源（1.内部服务，2.外部服务）
        @apiParam {Dict} pod_label POD模板标签
        @apiParam {Number} service_type 服务类型（1.集群内访问，2.集群内外部可访问，3.负载均衡器）
        @apiParam {String} clusterIP 集群IP
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
            self.guarantee('app_name', 'service_name', 'service_source', 'service_type')

            service_name = self.params['app_name'] + "-" + self.params['service_name']

            yaml_json = {
                            'apiVersion': 'v1',
                            'kind': 'Service',
                            'metadata': {
                                'name': service_name,
                                'labels': {
                                    'lord_app': self.params['app_name']
                                }
                            },
                            'spec': {
                                'type': K8S_SERVICE_TYPE[self.params['service_type']]
                            }
            }

            if self.params.get('pod_label'):
                yaml_json['spec']['selector'] = self.params['pod_label']

            if self.params.get('ports'):
                yaml_json['spec']['ports'] = self.params['ports']

            if self.params.get('clusterIP'):
                yaml_json['spec']['clusterIP'] = self.params['clusterIP']

            if self.params.get('externalIPs'):
                yaml_json['spec']['externalIPs'] = self.params['externalIPs']

            result = yaml.dump(yaml_json, default_flow_style=False)
            self.success(result)

