__author__ = 'Zhang'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler


class ImagehubHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 获取镜像仓库列表
        '''
        try:
            result = yield self.imagehub_service.get_list()

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())

class ImagehubBySourceHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 通过来源获取镜像仓库列表
        '''
        try:
            source_id = int(self.params['source'])
            result = yield self.imagehub_service.get_by_source(source_id)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())

class ImagehubByTypeHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 通过类型获取镜像仓库列表
        '''
        try:
            type_id = int(self.params['type'])
            result = yield self.imagehub_service.get_by_type(type_id)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())