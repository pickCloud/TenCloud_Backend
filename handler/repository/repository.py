__author__ = 'Jon'

import traceback
from handler.base import BaseHandler
from tornado.gen import coroutine, Task
from utils.decorator import is_login
from utils.context import catch
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
        with catch(self):
            token = self.redis.hget(GIT_TOKEN, str(self.current_user['id']))
            if not token:
                url = yield self.repos_service.auth_callback(self.params['url'], self.current_user['id'])
                self.error(message='Require token!', code=401, data={'url': url})
                return

            result = yield self.repos_service.fetch_repos(token)

            self.success(result)


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
        with catch(self):
            token = self.redis.hget(GIT_TOKEN, str(self.current_user['id']))

            if not token:
                url = yield self.repos_service.auth_callback(self.params['url'], self.current_user['id'])
                self.error(message='Require token!', code=401, data={'url': url})
                return

            repos_name = (self.params.get('repos_name') or '').strip()

            result = yield self.repos_service.fetch_branches(repos_name, token)

            self.success(result)


class GithubOauthCallbackHandler(BaseHandler):
    @coroutine
    def get(self):
        with catch(self):
            token = yield self.repos_service.fetch_token(self.params.get('code'))

            if token:
                self.redis.hset(GIT_TOKEN, str(self.params.get('uid')), token)

            url = self.get_argument('redirect_url')
            self.redirect(url=url, permanent=False, status=302)


class GithubOauthClearHandle(BaseHandler):
    @coroutine
    def post(self):
        """
        @api {post} /api/github/clear 清除github的授权
        @apiName GithubOauthClearHandle
        @apiGroup Repository

        @apiUse cidHeader

        @apiUse Success
        """
        with catch(self):
            self.redis.hdel(GIT_TOKEN, str(self.current_user['id']))
            self.success()
