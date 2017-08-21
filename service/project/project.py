__author__ = 'Jon'

import os
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor
from service.base import BaseService
from constant import CREATE_IMAGE_CMD, IMAGE_INFO_CMD, DEPLOY_CMD, \
                     REPOS_DOMAIN, LIST_CONTAINERS_CMD, LOAD_IMAGE_FILE,\
                     LOAD_IMAGE, CLOUD_DOWNLOAD_IMAGE
from setting import settings


class ProjectService(BaseService):
    table = 'project'
    fields = """
                id, name, description, repos_name, 
                repos_url, http_url, image_name, mode, status, 
                deploy_ips, container_name, image_source
            """

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
            container_name=params['container_name'])
        has_err = False
        log = dict()
        for ip in params['infos']:
            out, err = yield self.remote_ssh(ip, cmd)
            if err:
                has_err = True
            log[ip['public_ip']] = {"output": out, "error": err}
        return {'log': log, 'has_err': has_err}

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
    def update_status(self, params):
        sql = 'UPDATE {table} SET status=%s WHERE '.format(table=self.table)
        conds, arg = [], [params['status']]
        if params.get('id'):
            conds.append('id=%s')
            arg.append(params['id'])
        if params.get('name'):
            conds.append('name=%s')
            arg.append(params['name'])
        sql += ' AND '.join(conds)
        yield self.db.execute(sql, arg)

    @coroutine
    def list_containers(self, params):
        sufix = '|grep {container_name} '.format(container_name=params['container_name'])
        cmd = LIST_CONTAINERS_CMD+sufix
        out, err = yield self.remote_ssh(params, cmd)

        if err:
            raise ValueError

        data = [i.split(',') for i in out]

        return data

    @coroutine
    def insert_log(self, params):
        sql = """
                INSERT INTO project_versions (name, version, log) VALUES (%s, %s, %s) 
                ON DUPLICATE key UPDATE log=%s, update_time=NOW()
              """
        arg = [params['name'], params['version'], params['log'], params['log']]
        yield self.db.execute(sql, arg)

    @run_on_executor
    def upload_image(self, filename):
        filename = settings['store_path']+os.path.sep+filename
        cmd = LOAD_IMAGE_FILE.format(filename=filename)+LOAD_IMAGE
        out = os.system(cmd)
        if out:
            self.log.error(cmd)
            raise ValueError('failed to load image')

    @run_on_executor
    def cloud_download(self, image_url):
        cmd = CLOUD_DOWNLOAD_IMAGE.format(store_path=settings['store_path'], image_url=image_url)
        out = os.system(cmd)
        if out:
            self.log.error(cmd)
            raise ValueError('failed to cloud download image')



