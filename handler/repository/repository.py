__author__ = 'Jon'

import traceback
from handler.base import BaseHandler
from tornado.gen import coroutine
from utils.decorator import is_login


class RepositoryHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/repos 获取repos
        @apiName RepositoryHandler
        @apiGroup Repository

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
             {
                "status": 0,
                "msg": "success",
                 "data":[
                     {"repos_name": str, "repos_url": str, "http_url": str},
                     ...
                  ]
             }
        """
        try:
            result = yield self.repos_service.fetch_repos()

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class RepositoryBranchHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/repos/branches?repos_name='' 获取仓库的分支
        @apiName RepositoryBranchHandler
        @apiGroup Repository

        @apiParam {String} repos_name 仓库名称

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"branch_name": str},
                    ...
                ]
            }
        """
        try:
            repos_name = self.get_argument('repos_name', '').strip()

            result = yield self.repos_service.fetch_branches(repos_name)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class GithubOauthCallbackHandler(BaseHandler):
    @coroutine
    def get(self):
        try:
            code = self.get_argument('code')
            token = yield self.repos_service.fetch_token(code)

            print('token: {token}'.format(token=token))

        except:
            self.error()
            self.log.error(traceback.format_exc())