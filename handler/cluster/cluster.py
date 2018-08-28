__author__ = 'Jon'

import json

from tornado.gen import coroutine, Task
from handler.base import BaseHandler
from constant import CLUSTER_SEARCH_TIMEOUT, MSG_PAGE_NUM
from utils.decorator import is_login
from utils.context import catch


class ClusterHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/clusters 获取集群列表
        @apiName ClusterHandler
        @apiGroup Cluster

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": [
                    {"id": int, "name": str, "description": str},
                    ...
                ]
            }
        """
        with catch(self):
            result = yield self.cluster_service.select()

            self.success(result)


class ClusterDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, id):
        """
         @api {get} /api/cluster/(\d+) 集群详情
         @apiName ClusterDetailHandler
         @apiGroup Cluster

         @apiParam {Number} id 集群id
         @apiParam {Number} page
         @apiParam {Number} page_num

         @apiSuccessExample {json} Success-Response:
             HTTP/1.1 200 OK
             {
                 "status": 0,
                 "message": "success",
                 "data": {
                 "basic_info": {
                     "id": int,
                     "name": str,
                     "description": str,
                     "update_time": str
                 },
                 "server_list": [
                     {
                         "id": int,
                         "name": str,
                         "address": str,
                         "public_ip": str,
                         "machine_status": int,
                         "business_status": int,
                         "disk": str,
                         "memory": str,
                         "cpu": str,
                         "net": str,
                         "time": int
                     }
                        ...
                 ]
             }
         """
        with catch(self):
            id = int(id)

            basic_info = yield self.cluster_service.select({'id': id}, ct=False)
            server_list = yield self.server_service.get_brief_list(cluster_id=id, **self.get_lord())

            server_list = yield self.filter(server_list)

            page = int(self.params.get('page', 1))
            page_num = int(self.params.get('page_num', MSG_PAGE_NUM))

            self.success({
                'basic_info': basic_info,
                'server_list': server_list[page_num*(page-1):page_num*page]
            })


class ClusterNewHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/cluster/new 创建集群
        @apiName ClusterNewHandler
        @apiGroup Cluster

        @apiUse cidHeader

        @apiParam {[]Number} ids 主机id列表（第一个为集群Master的主机ID）
        @apiParam {String} name 集群名字
        @apiParam {Number} type 集群类型(1.Kubernetes集群 2.超级计算能力 2.高可用)
        @apiParam {Number} [num] 节点数量
        @apiParam {String} description 集群描述

        @apiUse Success
        """
        with catch(self):
            self.guarantee('ids', 'name', 'type', 'num', 'description')
            duplicate = yield self.cluster_service.select({'name': self.params.get('name', '')}, one=True)
            if duplicate:
                self.error('已有重复名称的集群存在，请换用其他名称')
                return

            cluster_info = yield self.cluster_service.add({'name': self.params['name'],
                                                           'description': self.params['description'],
                                                           'type': int(self.params['type']),
                                                           'master_server_id': self.params['ids'][0]})
            if cluster_info:
                cluster_id = cluster_info.get('id', 0)
                param = self.get_lord()
                for server_id in self.params['ids']:
                    param['id'] = server_id
                    yield self.server_service.update(sets={'cluster_id': cluster_id}, conds=param)

            self.success(cluster_info)


class ClusterWarnServerHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, id):
        """
         @api {get} /api/cluster/warn/(\d+) 需要提醒的机器信息
         @apiName ClusterWarnServerHandler
         @apiGroup Cluster

         @apiParam {Number} id 集群id

         @apiSuccessExample {json} Success-Response:
             HTTP/1.1 200 OK
             {
                 "status": 0,
                 "message": "success",
                 "data": [
                     {
                         "id": int,
                         "name": str,
                         "address": str,
                         "public_ip": str,
                         "machine_status": int,
                         "business_status": int,
                         "disk": str,
                         "memory": str,
                         "cpu": str,
                         "net": str,
                         "time": int
                     }
                        ...
                 ]
             }
         """
        with catch(self):
            server_list = yield self.server_service.get_brief_list(cluster_id=id, **self.get_lord())
            server_list = yield self.filter(server_list)

            # 检查并返回存在异常情况的机器数据
            result = []
            for server in server_list:
                for i in ['cpu', 'memory', 'disk']:
                    if server[i].get('percent') > 80:
                        result.append(server)
                        break

            # 如果没有异常机器，则直接返回CPU占用率前三高的机器
            if not result:
                result = sorted(server_list, key=lambda x: x['cpu']['percent'], reverse=True)[0:3]

            self.success(result)


class ClusterAllProviders(BaseHandler):
    @is_login
    @coroutine
    def get(self, cluster_id):
        """
        @api {get} /api/cluster/(\d+)/providers 获取该集群下所有提供商
        @apiName ClusterAllProviders
        @apiGroup Cluster

        @apiParam {Number} cluster_id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": [
                    {"provider": str,"regions": []str}
                    ...
                ]
            }
        """
        with catch(self):
            cluster_id = int(cluster_id)
            data = yield self.cluster_service.get_all_providers(cluster_id)
            self.success(data)


class ClusterSearchHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/cluster/search 服务器搜索
        @apiName ClusterSearchHandler
        @apiGroup Cluster

        @apiParam {Number} cluster_id
        @apiParam {String} server_name
        @apiParam {[]String} region_name
        @apiParam {[]String} provider_name
        @apiParam {Number} page
        @apiParam {Number} page_num

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": [
                    {}
                    ...
                ]
            }
        """
        with catch(self):
            cluster_id = self.params.get('cluster_id', 0)
            region_name = self.params.get('region_name', [])
            provider_name = self.params.get('provider_name', [])
            server_name = self.params.get('server_name', '')
            page = int(self.params.get('page', 1))
            page_num = int(self.params.get('page_num', MSG_PAGE_NUM))

            if not(server_name or provider_name or region_name):
                data = yield self.server_service.get_brief_list(
                    cluster_id=cluster_id,
                    provider=provider_name,
                    region=region_name,
                    **self.get_lord()
                )
                data = yield self.filter(data)
                self.success(data[page_num*(page-1):page_num*page])
                return

            data = yield self.server_service.get_brief_list(
                                                            cluster_id=cluster_id,
                                                            provider=provider_name,
                                                            region=region_name,
                                                            **self.get_lord()
                                                            )
            if server_name:
                data = self.cluster_service.select_by_name(data=data, server_name=server_name)

            data = yield self.filter(data)

            self.success(data[page_num*(page-1):page_num*page])


class ClusterSummaryHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/cluster/summary 服务器总览
        @apiName ClusterSummaryHandler
        @apiGroup Cluster

        @apiUse cidHeader

        @apiSuccessExample {json} Success-Response:
         HTTP/1.1 200 OK
         {
             "status": 0,
             "message": "success",
             "data": {
                 "server_num": 3,
                 "warn_num": 0,
                 "payment_num": 0
             }
         }
        """
        with catch(self):

            server = yield self.server_service.select(conds=self.get_lord())
            server = yield self.filter(server)

            data = {
                'server_num': len(server),
                'warn_num': 0,
                'payment_num': 0
            }
            self.success(data)


class ClusterNodeListHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/cluster/node 集群Node列表数据
        @apiName ClusterNodeListHandler
        @apiGroup Cluster

        @apiParam {Number} cluster_id 集群ID，不传代表获取所有集群列表

        @apiUse cidHeader

        @apiSuccessExample {json} Success-Response:
         HTTP/1.1 200 OK
         {
             "status": 0,
             "message": "success",
             "data": {[
                 "id": 37,
                 "type": 1,     # 集群类型(1.Kubernetes集群 2.超级计算能力 2.高可用)
                 "description": "test",
                 "master_server_id": 193,
                 "public_ip": "1.1.1.1",
                 "k8s_node": "apiVersion: v1..."    # K8s Node信息，YAML格式
             }],
             ...
         }
        """
        with catch(self):
            cluster_id = self.params.get('id', None)
            data = yield self.cluster_service.get_node_list(cluster_id)

            self.success(data)
