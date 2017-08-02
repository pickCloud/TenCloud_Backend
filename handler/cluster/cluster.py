__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
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
        except:
            self.error()
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
        except:
            self.error()
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
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ClusterDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, id):
        """
         @api {get} /api/clusters/(\d+) 集群详情
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
                         "business_status": int
                     }
                        ...
                 ]
             }
         """
        try:
            id = int(id)

            basic_info = yield self.cluster_service.select(conds=['id=%s'], params=[id], ct=False)
            server_list = yield self.server_service.get_brief_list(id)

            for s in server_list:
                s['address'] = ALIYUN_REGION_NAME.get(s['address'])

            self.success({
                'basic_info': basic_info,
                'server_list': server_list
            })
        except:
            self.error()
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
        except:
            self.error()
            self.log.error(traceback.format_exc())