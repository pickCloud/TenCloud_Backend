__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import CREATE_IMAGE_CMD


class ProjectService(BaseService):
    table  = 'project'
    fields = 'id, name, description, repos_name, repos_url'

    @coroutine
    def create_image(self, params):
        '''
        :param params: dict e.g. {'prj_name': str, 'repos_url': str, 'branch_name': str, 'public_ip': str, 'username': str, 'passwd': str}
        '''

        cmd = CREATE_IMAGE_CMD + ' -s ' + ' '.join([params['prj_name'], params['repos_url'], params['branch_name']])

        yield self.remote_ssh(params, cmd)