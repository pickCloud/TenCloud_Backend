__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from setting import settings
from constant import GIT_REPOS_URL


class RepositoryService(BaseService):
    headers = {'Authorization': 'token {}'.format(settings['git_token'])}

    @coroutine
    def fetch_repos(self):
        data = yield self.get(host=GIT_REPOS_URL, headers=self.headers)

        result = [{'clone_url': d.get('clone_url', ''),
                   'full_name': d.get('full_name', '')} for d in data]

        return result