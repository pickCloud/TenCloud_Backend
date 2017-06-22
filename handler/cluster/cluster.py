__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from constant import ALIYUN_REGION_NAME
from utils.general import get_in_formats


class ClusterHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 获取列表
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
        ''' 新建
            参数:
                {"name":        名称 str,
                 "description": 描述 str}
        '''
        try:
            result = yield self.cluster_service.add(self.params)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ClusterDelHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 删除
            参数:
               id -> list
        '''
        try:
            ids = self.params['id']

            yield self.cluster_service.delete(conds=[get_in_formats('id', ids)], params=ids)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ClusterDetailHandler(BaseHandler):
    @coroutine
    def get(self, id):
        ''' 详情
        '''
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
    @coroutine
    def post(self):
        ''' 更新
        '''
        try:
            sets = ['name=%s', 'description=%s']
            conds = ['id=%s']
            params = [self.params['name'], self.params['description'], self.params['id']]

            yield self.cluster_service.update(sets=sets, conds=conds, params=params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())