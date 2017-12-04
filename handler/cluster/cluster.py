__author__ = 'Jon'

import traceback
import json

from tornado.gen import coroutine, Task
from handler.base import BaseHandler
from constant import ALIYUN_REGION_NAME
from utils.general import get_in_formats
from utils.decorator import is_login


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
        try:
            result = yield self.cluster_service.select()

            self.success(result)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class ClusterNewHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/cluster/new 新建集群
        @apiName ClusterNewHandler
        @apiGroup Cluster

        @apiParam {String} name 名称
        @apiParam {String} description 描述

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": {
                    "id": int,
                    "update_time": str
                }
            }
        """
        try:
            result = yield self.cluster_service.add(self.params)

            self.success(result)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class ClusterDelHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/cluster/del 删除集群
        @apiName ClusterDelHandler
        @apiGroup Cluster

        @apiParam {Number} id 集群id

        @apiUse Success
        """
        try:
            ids = self.params['id']

            yield self.cluster_service.delete(conds=[get_in_formats('id', ids)], params=ids)

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


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
                         "disk_content": str,
                         "memory_content": str,
                         "cpu_content": str,
                         "net_content": str,
                     }
                        ...
                 ]
             }
         """
        try:
            id = int(id)

            basic_info = yield self.cluster_service.select(conds=['id=%s'], params=[id], ct=False)
            server_list = yield self.server_service.get_brief_list(cluster_id=id)
            self.success({
                'basic_info': basic_info,
                'server_list': server_list
            })
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

class ClustergAllProviders(BaseHandler):
    @is_login
    @coroutine
    def get(self, cluster_id):
        """
        @api {get} /api/cluster/(\d+)/providers 获取该集群下所有提供商
        @apiName ClustergAllProviders
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
        try:
            cluster_id = int(cluster_id)
            data = yield self.cluster_service.get_all_providers(cluster_id)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


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
<<<<<<< HEAD
        @apiParam {[]String} region_name
        @apiParam {[]String} provider_name
=======
        @apiParam {String} region_name
        @apiParam {String} provider_name
>>>>>>> 4f594a185d8f76fdcedd7622de9d075398e77cf5

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
        try:
            cluster_id = self.params['cluster_id']
            region_name = self.params.get('region_name', [])
            provider_name = self.params.get('provider_name', [])
            server_name = self.params.get('server_name', '')

            if not(server_name or provider_name or region_name):
                key = 'cluster_{id}'.format(id=str(cluster_id))
                data = yield Task(self.redis.get, key)
                if not data:
                    data = yield self.server_service.get_brief_list(
                        cluster_id=cluster_id,
                        provider=provider_name,
                        region=region_name
                    )
                    data = json.dumps(data)
                    yield Task(self.redis.setex, key, 60, data)
                self.success(json.loads(data))
                return

            data = yield self.server_service.get_brief_list(
                                                            cluster_id=cluster_id,
                                                            provider=provider_name,
                                                            region=region_name
                                                            )
            if server_name:
                data = yield self.cluster_service.select_by_name(data=data, server_name=server_name)
            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class ClusterUpdateHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/cluster/update 更新集群
        @apiName ClusterUpdateHandler
        @apiGroup Cluster

        @apiParam {Number} id 集群id
        @apiParam {String} name 名称
        @apiParam {String} description 描述

        @apiUse Success
        """
        try:
            sets = ['name=%s', 'description=%s']
            conds = ['id=%s']
            params = [self.params['name'], self.params['description'], self.params['id']]

            yield self.cluster_service.update(sets=sets, conds=conds, params=params)

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())