__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler


class ClusterHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 获取集群列表
        '''
        try:
            result = yield self.cluster_service.select()

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ClusterNewHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 创建新集群
            参数:
                name -> 集群名称 str
                desc -> 集群描述 str
        '''
        try:
            result = yield self.cluster_service.add_cluster(self.params)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ClusterDelHandler(BaseHandler):
    @coroutine
    def post(self):
        '''删除集群
           参数:
               id -> 集群id list
        '''
        try:
            yield self.cluster_service.del_cluster(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ClusterDetailHandler(BaseHandler):
    @coroutine
    def get(self, id):
        '''集群详情
           参数:
               id -> 集群id int
        '''
        try:
            id = int(id)

            basic_info = yield self.cluster_service.select(conds=['id=%s'], params=[id], ct=False)
            server_list = yield self.server_service.select(conds=['cluster_id=%s'], params=[id], ct=False)

            self.success({
                'basic_info': basic_info,
                'server_list': server_list
            })
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ClusterUpdateHandler(BaseHandler):
    @coroutine
    def post(self):
        try:
            yield self.cluster_service.update_cluster(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())