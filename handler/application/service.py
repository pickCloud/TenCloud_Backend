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
                     SERVICE_STATUS, DEPLOYMENT_TYPE, K8S_SERVICE_TYPE, SERVICE_SOURCE_TYPE, K8S_APPLY_CMD


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
        @apiParam {Number} [get_default] 获取默认模板
        @apiParam {Dict} [labels] 服务标签
        @apiParam {Number} service_source 服务来源（1.内部服务，通过标签选择，2.外部服务，通过IP映射，3.外部服务，通过别名映射）
        @apiParam {Dict} [selector_label] 内部服务选择标签（当服务来源选择1内部服务时使用）
        @apiParam {Dict{'ip': String, 'port': Number}} [externalIpMap] 外部服务IP（当服务来源选择2.外部服务，通过IP映射时使用）
        @apiParam {String} [externalName] 外部服务别名（当服务来源选择3.外部服务，通过别名映射时使用）
        @apiParam {String} [namespace] 外部服务命名空间（当服务来源选择3.外部服务，通过别名映射时使用）
        @apiParam {Number} [service_type] 服务类型（1.集群内访问，2.集群内外部可访问，3.负载均衡器）
        @apiParam {String} [clusterIP] 集群IP
        @apiParam {String} [loadBalancerIP] 负载均衡器IP
        @apiParam {[]String} [externalIPs] 外部IP
        @apiParam {[]{'name': String, 'protocol': String, 'port': Number, 'targetPort': Number}} [ports] 端口

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": "yaml"
            }
        """
        with catch(self):
            if self.params.get('get_default'):
                self.guarantee('app_id', 'app_name', 'service_name')
            else:
                self.guarantee('app_id', 'app_name', 'service_name', 'service_source')

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
                            }
            }
            yaml_ep = ''

            if self.params.get('get_default'):
                yaml_json['spec']['selector'] = {'app': 'default'}
                yaml_json['spec']['ports'] = [{'name': 'default', 'protocol': 'TCP', 'port': 80, 'targetPort': 80}]

            if self.params.get('ports'):
                yaml_json['spec']['ports'] = self.params['ports']

            if self.params.get('clusterIP'):
                yaml_json['spec']['clusterIP'] = self.params['clusterIP']

            if self.params.get('externalIPs'):
                yaml_json['spec']['externalIPs'] = self.params['externalIPs']

            if self.params.get('loadBalancerIP'):
                yaml_json['spec']['loadBalancerIP'] = self.params['loadBalancerIP']

            if self.params.get('service_type'):
                yaml_json['spec']['type'] = K8S_SERVICE_TYPE[self.params['service_type']]

            source_type = self.params.get('service_source', 0)
            if source_type == SERVICE_SOURCE_TYPE['by_label']:
                self.guarantee('selector_label')
                yaml_json['spec']['selector'] = self.params.get('selector_label', {})
            elif source_type == SERVICE_SOURCE_TYPE['by_cname']:
                self.guarantee('externalName')
                yaml_json['spec']['type'] = 'ExternalName'
                yaml_json['spec']['externalName'] = self.params.get('externalName', '')
            elif source_type == SERVICE_SOURCE_TYPE['by_ip']:
                self.guarantee('externalIpMap')
                yaml_ep_json = {
                    'apiVersion': 'v1',
                    'kind': 'Endpoints',
                    'metadata': {
                        'name': self.params['service_name'],
                        'labels': {
                            'internal_name': service_name,
                            'app_id': str(self.params['app_id'])
                        }
                    },
                    'subsets':[
                        {
                            'addresses': [{'ip': self.params['externalIpMap'].get('ip', 'default_ip')}],
                            'ports': [{'port': self.params['externalIpMap'].get('port', 'default_port')}]
                        }
                    ]
                }
                yaml_ep = yaml.dump(yaml_ep_json, default_flow_style=False)


            result = yaml.dump(yaml_json, default_flow_style=False)
            if yaml_ep:
                result += '\r\n---\r\n'
                result += yaml_ep

            self.success(result)


class K8sServiceHandler(WebSocketBaseHandler):
    def delete_service(self, params, out_func=None):
        param = params
        param['obj_type'] = 'service'
        service_info = self.service_service.sync_select({'id': params['service_id']}, one=True)
        param['obj_name'] = service_info['name']
        out, err = self.k8s_delete(param, out_func)
        self.service_service.sync_delete({'id': params['service_id']})
        return out, err

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
                if duplicate['id'] != int(self.params.get('service_id', 0)):
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
            if self.params.get('service_id'):
                login_info['service_id'] = self.params.get('service_id')
                self.delete_service(params=login_info, out_func=self.write_message)
            out, err = self.k8s_apply(params=login_info, out_func=self.write_message)

            # 生成部署数据
            log = {"out": out, "err": err}
            arg = {'name': self.params['service_name'], 'app_id': self.params['app_id'],
                   'type': int(self.params.get('service_type', K8S_SERVICE_TYPE.index('ClusterIP'))),
                   'state': SERVICE_STATUS['failure'] if err else SERVICE_STATUS['success'],
                   'yaml': self.params['yaml'], 'log': json.dumps(log)}
            arg.update(self.get_lord())
            if self.params.get('service_id'):
                arg['id'] = self.params.get('service_id')
            index = self.service_service.sync_add(arg)
            self.write_message('service ID:' + str(index))

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

class ServiceDeleteHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/service/delete 删除服务
        @apiName ServiceDeleteHandler
        @apiGroup Service

        @apiUse cidHeader

        @apiParam {Number} service_id 服务ID
        @apiParam {Number} app_id 应用ID

        @apiUse Success
        """
        with catch(self):
            self.guarantee('service_id')

            param = self.get_lord()
            param['id'] = self.params['service_id']
            service_info = yield self.service_service.select(conds=param, one=True)
            service_name = service_info.get('name', '') if service_info else None
            param['id'] = self.params['app_id']
            app_info = yield self.application_service.select(conds=param, one=True)

            if service_name and app_info:
                ssh_info = yield self.application_service.fetch_ssh_login_info({'server_id': app_info['server_id']})

                ssh_info['cmd'] = 'kubectl delete service ' + service_name
                yield self.service_service.remote_ssh(ssh_info)
                yield self.service_service.delete({'id': self.params['service_id']})
                self.success()
            else:
                self.error()


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


class ServicePortListHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/service/service_port 服务端口信息
        @apiName ServicePortListHandler
        @apiGroup Service

        @apiUse cidHeader

        @apiParam {Number} app_id 应用ID

        @apiDescription 样例: /api/service/service_port?app_id=\d

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "name": str,
                        "port": int,           // 端口号
                    },
                    ...
                ]
            }
        """
        with catch(self):
            self.guarantee('app_id')

            param = self.get_lord()
            param['app_id'] = int(self.params.get('app_id'))

            fields = "id, name, app_id, type, source, state, verbose"
            service_info = yield self.service_service.select(conds=param, fields=fields)
            service_port = []

            for svc in service_info:
                verbose = svc.get('verbose', None)
                verbose = yaml.load(verbose) if verbose else None
                if verbose:
                    ports = verbose['spec'].get('ports', [])
                    for port in ports:
                        service_port.append({'name': svc.get('name', ''), 'port': port.get('port', 0)})

            self.success(service_port)


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
                        "app_name": str,    //应用名称
                        "type": int,        //服务类型（1.集群内访问，2.集群内外部可访问，3.负载均衡器）
                        "state": int,       //状态
                        "labels": {'name': str, 'subsets': [{'addresses': [{'ip': str}], 'ports': [{'name': str, 'port': int, 'protocol': str}]}]},     //服务标签
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
                app_info = yield self.application_service.select({'id': i.get('app_id', 0)}, one=True)
                i['app_name'] = app_info.get('name', '') if app_info else ''

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
                            address['addresses'] = [{'ip': ip.get('ip', '')} for ip in address.get('addresses', [])]

            self.success(brief[page_num * (page - 1):page_num * page])


class IngressInfolHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/ingress/info Ingress信息
        @apiName IngressInfolHandler
        @apiGroup Service

        @apiUse cidHeader

        @apiParam {Number} app_id 应用ID
        @apiParam {Number} [show_detail] 是否查询默认后端、控制器等详情(0.否 1.是)

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "id": int,
                    "name": str,
                    "app_id": int,      //应用ID
                    "ip": str,          //Ingress IP地址
                    "rules": []{'host': str, 'paths': []{'serviceName': str, 'servicePort': int, 'path': str}}, //访问规则
                    "backend": {'serviceName': str, 'servicePort': int, 'app_name': str, 'app_id': int},    //默认后端
                    "controller": {'serviceName': str, 'servicePort': int, 'app_name': str, 'app_id': int}, //控制器
                    "form": int,
                    "lord": int,
                    "create_time": str,
                    "update_time"" str
                }
            }
        """
        with catch(self):
            self.guarantee('app_id')

            ingress_info = yield self.ingress_service.select({'app_id': self.params['app_id']}, one=True)
            verbose = ingress_info.pop('verbose', None) if ingress_info else None
            verbose = yaml.load(verbose) if verbose else None
            if verbose:
                ingress_info['ip'] = ''
                ingress_info['rules'] = [{'host': rule.get('host', ''),
                                          'paths': [{'path': path.get('path', '/'),
                                                     'serviceName': path.get('backend', {}).get('serviceName', ''),
                                                     'servicePort': path.get('backend', {}).get('servicePort', 0)}
                                                    for path in rule.get('http', {}).get('paths', [])]}
                                         for rule in verbose['spec'].get('rules', [])]
                if self.params.get('show_detail'):
                    ingress_backend = yield self.application_service.select({'master_app': self.params['app_id'],
                                                                             'name': 'Ingress-default-backend'},
                                                                            one=True)
                    ingress_info['backend'] = {'serviceName': 'ingress-default-backend', 'servicePort': 80,
                                               'app_name': 'Ingress-default-backend',
                                               'app_id': ingress_backend['id'] if ingress_backend else 0}

                    ingress_controller = yield self.application_service.select({'master_app': self.params['app_id'],
                                                                                'name': 'Nginx-ingress-controller'},
                                                                               one=True)
                    ingress_info['controller'] = {'serviceName': 'nginx-ingress-controller', 'servicePort': 80,
                                                  'app_name': 'Nginx-ingress-controller',
                                                  'app_id': ingress_controller['id'] if ingress_controller else 0}

            self.success(ingress_info)


class IngressConfigHandler(BaseHandler):
    def save_yaml(self, app_name, obj_name, obj_type, yaml):
        full_path = os.path.join('/var/www/Dashboard/static', 'yaml')
        if not os.path.exists(full_path): os.makedirs(full_path)

        filename = app_name + "." + obj_name + "." + obj_type + ".yaml"
        fullname = os.path.join(full_path, filename)

        with open(fullname, 'wb') as f:
            f.write(yaml.encode())

        return filename

    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/ingress/config 配置ingress规则
        @apiName IngressConfigHandler
        @apiGroup Service

        @apiUse cidHeader

        @apiParam {Number} app_id 应用ID
        @apiParam {[]{'host': str, 'paths': []{'serviceName': str, 'servicePort': int, 'path': str}}} rules 规则

        @apiUse Success
        """
        with catch(self):
            self.guarantee('app_id', 'rules')

            ingress_name = 'ingress-' + str(self.params['app_id'])
            app_info = yield self.application_service.select({'id': self.params['app_id']}, one=True)
            app_name = app_info.get('name', 'default') if app_info else 'default'
            internal_name = app_name + '.' + ingress_name

            yaml_json = {
                'apiVersion': 'extensions/v1beta1',
                'kind': 'Ingress',
                'metadata': {
                    'name': ingress_name,
                    'labels': {
                        'internal_name': internal_name,
                        'app_id': str(self.params['app_id'])
                    },
                    'annotations': {
                        'nginx.ingress.kubernetes.io/add-base-url': 'true',
                        'nginx.ingress.kubernetes.io/rewrite-target': '/'
                    }
                },
                'spec': {
                    'rules': []
                }
            }

            for rule in self.params.get('rules', []):
                rule_item = {'host': rule.get('host', ''), 'http': {'paths': [{'path': path.get('path', '/'),
                                                                               'backend': {'serviceName': path.get(
                                                                                   'serviceName', ''),
                                                                                           'servicePort': int(path.get(
                                                                                               'servicePort', 0))}} for
                                                                              path in rule.get('paths', [])]}}
                yaml_json['spec']['rules'].append(rule_item)

            ingress_yaml = yaml.dump(yaml_json, default_flow_style=False)
            # 生成yaml文件并归档到服务器yaml目录下
            filename = self.save_yaml(app_name, ingress_name, 'ingress', ingress_yaml)

            ssh_info = yield self.application_service.fetch_ssh_login_info({'server_id': app_info['server_id']})
            ssh_info['cmd'] = K8S_APPLY_CMD + filename

            _, err = yield self.service_service.remote_ssh(ssh_info)

            if err:
                self.error()
            else:
                ingress_info = yield self.ingress_service.add({'name': ingress_name, 'app_id': self.params['app_id']})
                self.success(ingress_info)
