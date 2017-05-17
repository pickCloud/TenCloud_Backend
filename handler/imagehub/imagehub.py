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
            result = yield self.imagehub_service.get_by_source(self.params)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())