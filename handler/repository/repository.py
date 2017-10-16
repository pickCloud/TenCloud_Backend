__author__ = 'Jon'

import traceback
from handler.base import BaseHandler
from tornado.gen import coroutine, Task
from utils.decorator import is_login
from constant import GIT_TOKEN


class RepositoryHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/repos 获取repos
        @apiName RepositoryHandler
        @apiGroup Repository

        @apiParam {String} url 当前页面地址

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
            @apiErrorExample {json} Error-Response:
                HTTP/1.1 401 Unauthorized
                {
                    "status": 0,
                    "msg": "require token",
                    "data": {
                        "url": str
                    }
                }
        """
        try:
            token = yield Task(self.redis.hget, GIT_TOKEN, str(self.current_user['id']))
            if not token:
                url = yield self.repos_service.auth_callback(self.params['url'])
                self.error(message='Require token!', code=401, data={'url': url})
                return

            result = yield self.repos_service.fetch_repos(token)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class RepositoryBranchHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/repos/branches 获取仓库的分支
        @apiName RepositoryBranchHandler
        @apiGroup Repository

        @apiParam {String} repos_name 仓库名称
        @apiParam {String} url 当前页面地址

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

        @apiErrorExample {json} Error-Response:
             HTTP/1.1 401 Unauthorized
            {
                "status": 0,
                "msg": "require token",
                "data": {
                   "url": str
                }
            }
        """
        try:
            token = yield Task(self.redis.hget, GIT_TOKEN, str(self.current_user['id']))

            if not token:
                url = yield self.repos_service.auth_callback(self.params['url'])
                self.error(message='Require token!', code=401, data={'url': url})
                return

            repos_name = (self.params.get('repos_name') or '').strip()

            result = yield self.repos_service.fetch_branches(repos_name, token)

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

            yield Task(self.redis.hset, GIT_TOKEN, str(self.current_user['id']), token)
            url = self.get_argument('redirect_url')
            self.redirect(url=url, permanent=False, status=302)
        except:
            self.error()
            self.log.error(traceback.format_exc())