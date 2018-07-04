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
                     SERVICE_STATUS, DEPLOYMENT_TYPE, K8S_SERVICE_TYPE, SERVICE_SOURCE_TYPE


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
        @apiParam {Dict} [labels] 服务标签
        @apiParam {Number} service_source 服务来源（1.内部服务，通过标签选择，2.外部服务，通过IP映射，3.外部服务，通过别名映射）
        @apiParam {Dict} [selector_label] 内部服务选择标签（当服务来源选择1内部服务时使用）
        @apiParam {Dict{'ip': String, 'port': Number}} [externalIpMap] 外部服务IP（当服务来源选择2.外部服务，通过IP映射时使用）
        @apiParam {String} [externalName] 外部服务别名（当服务来源选择3.外部服务，通过别名映射时使用）
        @apiParam {String} [namespace] 外部服务命名空间（当服务来源选择3.外部服务，通过别名映射时使用）
        @apiParam {Number} service_type 服务类型（1.集群内访问，2.集群内外部可访问，3.负载均衡器）
        @apiParam {String} [clusterIP] 集群IP
        @apiParam {String} [loadBalancerIP] 负载均衡器IP
        @apiParam {[]String} [externalIPs] 外部IP
        @apiParam {[]{'name': String, 'protocol': String, 'port': Number, 'targetPort': Number}} ports 端口

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": "yaml"
            }
        """
        with catch(self):
            self.guarantee('app_id', 'app_name', 'service_name', 'service_source', 'service_type')

            service_name = self.params['app_name'] + "." + self.params['service_name']

            yaml_json = {
                            'apiVersion': 'v1',
                            'kind': 'Service',
                            'metadata': {
                                'name': self.params['service_name'],
                                'labels': {
                                    'internal_name': service_name,
                                    'app_id': str(self.params['app_id'])
                                }
                            },
                            'spec': {
                                'type': K8S_SERVICE_TYPE[self.params['service_type']]
                            }
            }

            if self.params.get('ports'):
                yaml_json['spec']['ports'] = self.params['ports']

            if self.params.get('clusterIP'):
                yaml_json['spec']['clusterIP'] = self.params['clusterIP']

            if self.params.get('externalIPs'):
                yaml_json['spec']['externalIPs'] = self.params['externalIPs']

            if self.params.get('loadBalancerIP'):
                yaml_json['spec']['loadBalancerIP'] = self.params['loadBalancerIP']

            source_type = self.params.get('service_source', 0)
            if source_type == SERVICE_SOURCE_TYPE['by_label']:
                self.guarantee('selector_label')
                yaml_json['spec']['selector'] = self.params.get('selector_label', {})
            elif source_type == SERVICE_SOURCE_TYPE['by_cname']:
                self.guarantee('externalName')
                yaml_json['spec']['type'] = 'ExternalName'
                yaml_json['spec']['externalName'] = self.params.get('externalName', '')

            result = yaml.dump(yaml_json, default_flow_style=False)
            self.success(result)


class K8sServiceHandler(WebSocketBaseHandler):
    def on_message(self, message):
        self.params.update(json.loads(message))

        try:
            args = ['app_id', 'app_name', 'service_name', 'service_type', 'service_source', 'yaml']
            self.guarantee(*args)
            validate_k8s_object_name(self.params['service_name'])

            # 检查服务名称是否冲突
            duplicate = self.service_service.sync_select({'name': self.params['service_name'],
                                                          'app_id': self.params['app_id']}, one=True)
            if duplicate:
                raise ValueError('该集群内已有同名服务运行，请换用其他名称')

            # 获取需要部署的主机IP
            app_info = self.application_service.sync_select({'id': self.params['app_id']}, one=True)
            server_id = app_info['server_id'] if app_info else 0
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
                   'type': int(self.params.get('service_type', K8S_SERVICE_TYPE.index('ClusterIP'))),
                   'state': SERVICE_STATUS['failure'] if err else SERVICE_STATUS['success'],
                   'yaml': self.params['yaml'], 'log': json.dumps(log)}
            arg.update(self.get_lord())
            index = self.service_service.sync_add(arg)
            self.write_message('service ID:' + index)

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


class ServiceBriefHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/service/brief 服务概况
        @apiName ServiceBriefHandler
        @apiGroup Service

        @apiUse cidHeader

        @apiParam {Number} app_id 应用ID
        @apiParam {Number} [state] 服务状态(1.未知, 2.成功, 3.失败)
        @apiParam {Number} [service_id] 服务ID(* 可选字段)
        @apiParam {Number} [page] 页数
        @apiParam {Number} [page_num] 每页显示项数

        @apiDescription 样例: /api/service/brief?app_id=\d&state=\d&page=\d&page_num=\d

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": int,
                        "name": str,
                        "state": int,           // service状态(1.未知, 2.成功, 3.失败)
                        "app_id": int,
                        "type": int,            // service类型(1.ClusterIP, 2.NodeIP, 3.LoadBalancer)
                        "source": int,          // 服务来源(1.集群内服务 2.集群外服务)
                    },
                    ...
                ]
            }
        """
        with catch(self):
            param = self.get_lord()

            if self.params.get('app_id'):
                param['app_id'] = int(self.params.get('app_id'))
            if self.params.get('state'):
                param['state'] = int(self.params.get('state'))
            if self.params.get('service_id'):
                param['id'] = int(self.params.get('service_id'))
            page = int(self.params.get('page', 1))
            page_num = int(self.params.get('page_num', MSG_PAGE_NUM))

            fields = "id, name, app_id, type, source, state"
            brief = yield self.service_service.select(conds=param, fields=fields)

            self.success(brief[page_num * (page - 1):page_num * page])

class ServiceDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/service/detail 服务详情
        @apiName ServiceDetailHandler
        @apiGroup Service

        @apiUse cidHeader

        @apiParam {Number} app_id 应用ID
        @apiParam {Number} [state] 服务状态(1.未知, 2.成功, 3.失败)
        @apiParam {Number} [service_id] 服务ID(* 可选字段)
        @apiParam {Number} [show_yaml] 是否查询yaml内容(0.否 1.是)
        @apiParam {Number} [show_log] 是否查询Log内容(0.否 1.是)
        @apiParam {Number} [page] 页数
        @apiParam {Number} [page_num] 每页显示项数

        @apiDescription 样例: /api/service/detail?app_id=\d&state=\d&page=\d&page_num=\d
                        or /api/service/detail?service_id=\d&

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": int,
                        "name": str,
                        "app_id": int,      //应用ID
                        "type": int,        //服务类型（1.集群内访问，2.集群内外部可访问，3.负载均衡器）
                        "state": int,       //状态
                        "labels": dict,     //服务标签
                        "source": int,      //服务来源（1.内部服务，通过标签选择，2.外部服务，通过IP映射，3.外部服务，通过别名映射）
                        "access": list,     //访问服务
                        "endpoint": dict,   //服务后端
                        "yaml": str,        //服务定义
                        "log": str,         //日志
                        "verbose": str,     //服务内部数据
                        "form": int,
                        "lord": int,
                        "create_time": str,
                        "update_time"" str
                    },
                    ...
                ]
            }
        """
        with catch(self):
            param = self.get_lord()

            if self.params.get('app_id'):
                param['app_id'] = int(self.params.get('app_id'))
            if self.params.get('state'):
                param['state'] = int(self.params.get('state'))
            if self.params.get('service_id'):
                param['id'] = int(self.params.get('service_id'))
            page = int(self.params.get('page', 1))
            page_num = int(self.params.get('page_num', MSG_PAGE_NUM))
            show_yaml = int(self.params.get('show_yaml', 0))
            show_log = int(self.params.get('show_log', 0))

            brief = yield self.service_service.select(conds=param)

            for i in brief:
                # 从k8s集群上报过来的yaml信息中解析出pod状态等信息
                verbose = i.pop('verbose', None)
                verbose = yaml.load(verbose) if verbose else None
                if verbose:
                    i['clusterIP'] = verbose['spec'].get('clusterIP', '')
                    i['externalIPs'] = verbose['spec'].get('externalIPs', '')
                    i['loadBalancerIP'] = verbose['spec'].get('loadBalancerIP', '')
                    i['ports'] = verbose['spec'].get('ports', '')
                    i['labels'] = verbose['metadata'].get('labels', {})

                    if verbose['spec'].get('type', '') == 'ClusterIP':
                        clusterIP = verbose['spec'].get('clusterIP', '')
                        i['access'] = [clusterIP+':'+str(item.get('port', '')) for item in verbose['spec'].get('ports', [])]
                    elif verbose['spec'].get('type', '') == 'NodePort':
                        pass
                    elif verbose['spec'].get('type', '') == 'LoadBalancer':
                        pass

                # 去除一些查询列表时用不到的字段
                if not show_log: i.pop('log', None)
                if not show_yaml: i.pop('yaml', None)

                # 获取endpoints信息
                i['endpoint'] = {}
                endpoint_info = yield self.endpoint_service.select({'service_id': i['id']}, one=True)
                if endpoint_info:
                    ep_verbose = yaml.load(endpoint_info['verbose']) if endpoint_info.get('verbose') else None
                    if ep_verbose:
                        i['endpoint'] = {'name': ep_verbose['metadata'].get('name', ''),
                                         'subsets': ep_verbose.get('subsets', [])}

                        for address in i['endpoint']['subsets']:
                            address['addresses'] = [{'ip': ip.get('ip', '')} for ip in address['addresses']]

            self.success(brief[page_num * (page - 1):page_num * page])