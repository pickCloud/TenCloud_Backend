__author__ = 'Jon'

from urllib.parse import urlencode
from tornado.gen import coroutine
from service.base import BaseService
from setting import settings
from constant import GIT_REPOS_URL, GIT_BRANCH_URL, GIT_FETCH_TOKEN_URL, GIT_CALLBACK, GIT_FETCH_CODE_URL


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
            'client_id' : settings['git_client_id'],
            'client_secret': settings['git_client_secret'],
            'code': code
        }

        result = yield self.post(GIT_FETCH_TOKEN_URL, params)

        return result.get('access_token')

    @coroutine
    def auth_callback(self, original_path):
        redirect_uri = GIT_CALLBACK + '?' + urlencode(
                {'redirect_url': original_path}
        )
        params = {
            'client_id': settings['git_client_id'],
            'scope': settings['git_scope'],
            'state': settings['git_state'],
            'redirect_uri': redirect_uri
        }
        url = GIT_FETCH_CODE_URL + '?' + urlencode(params)
        return url
