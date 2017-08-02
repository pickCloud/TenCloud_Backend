__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import CREATE_IMAGE_CMD, IMAGE_INFO_CMD, DEPLOY_CMD, REPOS_DOMAIN
from setting import settings


class ProjectService(BaseService):
    table = 'project'
    fields = 'id, name, description, repos_name, repos_url, http_url, image_name, mode, status, deploy_ips'

    @coroutine
    def create_image(self, params):
        '''
        :param params: dict e.g. {'prj_name': str, 'repos_url': str, 'branch_name': str, 'public_ip': str, 'username': str, 'passwd': str}
        '''

        cmd = CREATE_IMAGE_CMD + ' '.join([params['image_name'], params['repos_url'], params['branch_name'], params['version']])

        out, err = yield self.remote_ssh(params, cmd)
        return out, err

    @coroutine
    def deployment(self, params):
        image_name = REPOS_DOMAIN + "/library/" + params['image_name']
        cmd = DEPLOY_CMD.format(
            repository=REPOS_DOMAIN,
            username=settings['deploy_username'],
            password=settings['deploy_password'],
            image_name=image_name,
            container_name=params['image_name'].replace(":", "-"))
        log = dict()
        for ip in params['infos']:
            out, err = yield self.remote_ssh(ip, cmd)
            log[ip['public_ip']] = {"output": out, "error": err}
        return log

    @coroutine
    def find_image(self, params):
        """
        查找项目镜像
        """
        cmd = IMAGE_INFO_CMD % (params['prj_name'])
        out, err = yield self.remote_ssh(params, cmd)
        data = [i.split(',') for i in out]
        return data, err

    @coroutine
    def insert_log(self, params):
        sql = """
                INSERT INTO project_versions (name, version, log) VALUES (%s, %s, %s) 
                ON DUPLICATE key UPDATE log=%s, update_time=NOW()
              """
        arg = [params['name'], params['version'], params['log'], params['log']]
        yield self.db.execute(sql, arg)

