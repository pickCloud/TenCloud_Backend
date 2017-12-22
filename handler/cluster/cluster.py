__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.general import get_in_formats
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
        with catch(self):
            id = int(id)

            basic_info = yield self.cluster_service.select({'id': id}, ct=False)
            server_list = yield self.server_service.get_brief_list(id)

            self.success({
                'basic_info': basic_info,
                'server_list': server_list
            })


class ClusterSearchHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/cluster/search 集群名称
        @apiName ClusterSearchHandler
        @apiGroup Cluster

        @apiParam {Number} cluster_id
        :return:
        """
        pass