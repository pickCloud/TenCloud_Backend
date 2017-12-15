__author__ = 'Zhang'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login
from utils.context import catch


class ImagehubHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        ''' 获取镜像仓库列表
        '''
        with catch(self):
            result = yield self.imagehub_service.get_list()

            self.success(result)


class ImagehubBySourceHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        ''' 通过来源获取镜像仓库列表
        '''
        with catch(self):
            source_id = int(self.params['source'])
            result = yield self.imagehub_service.get_by_source(source_id)

            self.success(result)


class ImagehubByTypeHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        ''' 通过类型获取镜像仓库列表
        '''
        with catch(self):
            type_id = int(self.params['type'])
            result = yield self.imagehub_service.get_by_type(type_id)

            self.success(result)


class ImagehubSearchHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        ''' 通过搜索获取镜像仓库列表
        '''
        with catch(self):
            # 查询内容，名称，来源，类型
            query_data = {
                "name": self.params['name'],
                "source": self.params['source'],
                "type": tuple(self.params['type'])
            }
            result = yield self.imagehub_service.get_by_search(query_data)
            self.success(result)