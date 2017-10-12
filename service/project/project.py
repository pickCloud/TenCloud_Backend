__author__ = 'Jon'

import os
import re
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor
from service.base import BaseService
from utils.ssh import SSH
from utils.security import Aes
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

    def sync_db_execute(self, sql, params):
        try:
            with self.sync_db.cursor() as cur:
                cur.execute(sql, params)
            self.sync_db.commit()
        except:
            raise ValueError("sync_db_execute error with {sql}".format(sql=sql))

    def sync_db_fetchone(self, sql, params):
        try:
            with self.sync_db.cursor() as cur:
                cur.execute(sql, params)
                res = cur.fetchone()
            self.sync_db.commit()
        except:
            raise ValueError("sync_db_fetchone error with {sql}".format(sql=sql))
        return res

    def sync_update_status(self, params):
        sql = 'UPDATE {table} SET status=%s WHERE '.format(table=self.table)
        conds, arg = [], [params['status']]
        if params.get('id'):
            conds.append('id=%s')
            arg.append(params['id'])
        if params.get('name'):
            conds.append('name=%s')
            arg.append(params['name'])
        sql += ' AND '.join(conds)
        self.sync_db_execute(sql, arg)

    def sync_insert_log(self, params):
        sql = """
                INSERT INTO project_versions (name, version, log) VALUES (%s, %s, %s) 
                ON DUPLICATE key UPDATE log=%s, update_time=NOW()
              """
        arg = [params['name'], params['version'], params['log'], params['log']]
        self.sync_db_execute(sql, arg)

    def sync_fetch_ssh_login_info(self, params):
        sql = "SELECT s.public_ip, sa.username, sa.passwd FROM server s JOIN server_account sa USING(public_ip) WHERE "
        conds, data = [], []
        if params.get('server_id'):
            conds.append('s.id=%s')
            data.append(params['server_id'])

        if params.get('public_ip'):
            conds.append('s.public_ip=%s')
            data.append(params['public_ip'])

        sql += ' AND '.join(conds)
        res = self.sync_db_fetchone(sql, data)
        res['passwd'] = Aes.decrypt(res['passwd'])

        return res

    def create_image(self, params, out_func=None):
        cmd = CREATE_IMAGE_CMD + ' '.join([params['image_name'], params['repos_url'], params['branch_name'], params['version']])
        ssh = SSH(hostname=params['public_ip'], port=22, username=params['username'], passwd=params['passwd'])
        out, err = ssh.exec_rt(cmd, out_func)
        err = [e for e in str(err) if not re.search(r'From github.com|->', e)]
        return str(out), ''.join(err)

    def deployment(self, params, out_func=None):
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
            ssh = SSH(hostname=ip['public_ip'], port=22, username=ip['username'], passwd=ip['passwd'])
            out, err = ssh.exec_rt(cmd, out_func)
            if err:
                has_err = True
            log[ip['public_ip']] = {"output": str(out), "error": str(err)}
        return {'log': log, 'has_err': has_err}

    def set_deploy_ips(self, params):
        sql = """
                UPDATE {table} SET deploy_ips=%s, container_name=%s, status=%s
                WHERE id=%s
              """.format(table=self.table)
        self.sync_db_execute(sql, params)

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



