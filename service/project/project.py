__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import CREATE_IMAGE_CMD, IMAGE_INFO_CMD, DEPLOY_CMD, REPOS_DOMAIN
from setting import settings


class ProjectService(BaseService):
    table = 'project'
    fields = 'id, name, description, repos_name, repos_url, mode, status'

    @coroutine
    def create_image(self, params):
        '''
        :param params: dict e.g. {'prj_name': str, 'repos_url': str, 'branch_name': str, 'public_ip': str, 'username': str, 'passwd': str}
        '''

        cmd = CREATE_IMAGE_CMD + ' '.join([params['prj_name'], params['repos_url'], params['branch_name'], params['version']])

        yield self.remote_ssh(params, cmd)

    @coroutine
    def deployment(self, params):
        image_name = REPOS_DOMAIN + "/library/" + params['image_name']
        cmd = DEPLOY_CMD.format(
            repository=REPOS_DOMAIN,
            username=settings['deploy_username'],
            password=settings['deploy_password'],
            image_name=image_name)
        yield self.remote_ssh(params, cmd)

    @coroutine
    def find_image(self, params):
        """
        查找项目镜像
        """
        cmd = IMAGE_INFO_CMD % (params['prj_name'])
        out, err = yield self.remote_ssh(params, cmd)
        data = [i.split(',') for i in out]
        return data, err
