__author__ = 'Zhang'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login


class ImagehubHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        ''' 获取镜像仓库列表
        '''
        try:
            result = yield self.imagehub_service.get_list()

            self.success(result)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class ImagehubBySourceHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        ''' 通过来源获取镜像仓库列表
        '''
        try:
            source_id = int(self.params['source'])
            result = yield self.imagehub_service.get_by_source(source_id)

            self.success(result)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class ImagehubByTypeHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        ''' 通过类型获取镜像仓库列表
        '''
        try:
            type_id = int(self.params['type'])
            result = yield self.imagehub_service.get_by_type(type_id)

            self.success(result)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class ImagehubSearchHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        ''' 通过搜索获取镜像仓库列表
        '''
        try:
            # 查询内容，名称，来源，类型
            query_data = {
                "name": self.params['name'],
                "source": self.params['source'],
                "type": tuple(self.params['type'])
            }
            result = yield self.imagehub_service.get_by_search(query_data)
            self.success(result)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())