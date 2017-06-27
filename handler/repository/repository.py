__author__ = 'Jon'

import traceback
from handler.base import BaseHandler
from tornado.gen import coroutine


class RepositoryHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 获取repos, 现在默认git并且token保存在setting, 以后可以支持更多并且使用数据库
        '''
        try:
            result = yield self.repos_service.fetch_repos()

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class RepositoryBranchHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 获取仓库的分支
        '''
        try:
            repos_name = self.get_argument('repos_name', '').strip()

            result = yield self.repos_service.fetch_branches(repos_name)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())