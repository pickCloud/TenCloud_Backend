__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.general import get_in_formats


class ProjectHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 获取列表
        '''
        try:
            result = yield self.project_service.select(ct=False)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectNewHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 新建
            参数:
                {"name":        名称 str,
                 "description": 描述 str,
                 "repository":  仓库 str}
        '''
        try:
            result = yield self.project_service.add(params=self.params)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectDelHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 删除
            参数: {"id": list}
        '''
        try:
            ids = self.params['id']

            yield self.project_service.delete(conds=[get_in_formats('id', ids)], params=ids)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectDetailHandler(BaseHandler):
    @coroutine
    def get(self, id):
        ''' 详情
        '''
        try:
            result = yield self.project_service.select(conds=['id=%s'], params=[id])

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectUpdateHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 更新
        '''
        try:

            sets = ['name=%s', 'description=%s', 'repository=%s']
            conds = ['id=%s']
            params = [self.params['name'], self.params['description'], self.params['repository'], self.params['id']]

            yield self.project_service.update(sets=sets, conds=conds, params=params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())