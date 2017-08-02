__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from setting import settings
from constant import GIT_REPOS_URL, GIT_BRANCH_URL


class RepositoryService(BaseService):
    headers = {'Authorization': 'token {}'.format(settings['git_token'])}

    @coroutine
    def fetch_repos(self):
        ''' git账号下的所有仓库
        '''
        data = yield self.get(host=GIT_REPOS_URL, headers=self.headers)
        result = [{'repos_url': d.get('ssh_url', ''),
                   'repos_name': d.get('full_name', ''),
                   'http_url': d.get('clone_url', '')} for d in data]

        return result

    @coroutine
    def fetch_branches(self, repos_name):
        ''' 根据repos_name获取所有分支
        '''
        data = yield self.get(host=GIT_BRANCH_URL.format(repos_name=repos_name), headers=self.headers)

        result = [{'branch_name': d.get('name')} for d in data]

        return result
