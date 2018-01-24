__author__ = 'Jon'

import json

from tornado.gen import coroutine, Task
from handler.base import BaseHandler
from constant import CLUSTER_SEARCH_TIMEOUT
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
            result = yield self.cluster_service.select({'id': 1})

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

            self.success({
                'basic_info': basic_info,
                'server_list': server_list
            })


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
            cluster_id = self.params['cluster_id']
            region_name = self.params.get('region_name', [])
            provider_name = self.params.get('provider_name', [])
            server_name = self.params.get('server_name', '')

            if not(server_name or provider_name or region_name):
                key = 'cluster_{id}'.format(id=str(cluster_id))
                data = self.redis.get(key)
                if not data:
                    data = yield self.server_service.get_brief_list(
                        cluster_id=cluster_id,
                        provider=provider_name,
                        region=region_name,
                        **self.get_lord()
                    )
                    data = json.dumps(data)
                    self.redis.setex(key, CLUSTER_SEARCH_TIMEOUT, data)
                self.success(json.loads(data))
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

            self.success(data)
