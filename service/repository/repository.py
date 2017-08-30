__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from setting import settings
from constant import GIT_REPOS_URL, GIT_BRANCH_URL, GIT_FETCH_TOKEN_URL


class RepositoryService(BaseService):
    headers = {'Authorization': 'token {token}'}

    @coroutine
    def fetch_repos(self, token):
        ''' git账号下的所有仓库
        '''
        self.headers['Authorization'] = self.headers['Authorization'].format(token=token)

        data = yield self.get(host=GIT_REPOS_URL, headers=self.headers)
        result = [{'repos_url': d.get('ssh_url', ''),
                   'repos_name': d.get('full_name', ''),
                   'http_url': d.get('clone_url', '')} for d in data]

        return result

    @coroutine
    def fetch_branches(self, repos_name, token):
        ''' 根据repos_name获取所有分支
        '''
        self.headers['Authorization'] = self.headers['Authorization'].format(token=token)

        data = yield self.get(host=GIT_BRANCH_URL.format(repos_name=repos_name), headers=self.headers)

        result = [{'branch_name': d.get('name')} for d in data]

        return result

    @coroutine
    def fetch_token(self, code=None):
        '''
        :param code: given by github
        :return: token
        '''
        params = {
            'client_id' : settings['git_oauth_id'],
            'client_secret': settings['git_oauth_secret'],
            'code': code
        }

        result = yield self.post(GIT_FETCH_TOKEN_URL, params)

        return result.get('access_token')