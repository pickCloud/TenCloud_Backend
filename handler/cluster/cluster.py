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
            result = yield self.cluster_service.get_list()

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ClusterNewHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 创建新集群
            参数:
                name -> 集群名称
                desc -> 集群描述
        '''
        try:
            id = yield self.cluster_service.add_cluster(self.params)

            self.success(id)
        except:
            self.error()
            self.log.error(traceback.format_exc())