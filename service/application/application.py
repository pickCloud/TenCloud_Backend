
import os
import re
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor
from service.base import BaseService
from utils.ssh import SSH
from utils.security import Aes
from constant import CREATE_IMAGE_CMD, IMAGE_INFO_CMD, DEPLOY_CMD, \
                     REPOS_DOMAIN, LIST_CONTAINERS_CMD, LOAD_IMAGE_FILE,\
                     LOAD_IMAGE, CLOUD_DOWNLOAD_IMAGE, YE_PORTMAP, FULL_DATE_FORMAT_ESCAPE
from setting import settings

class ApplicationService(BaseService):
    table = 'application'
    fields = """
                id, name, description, status, master_app, server_id, repos_name, 
                repos_ssh_url, repos_https_url, logo_url, labels,
                image_id, lord, form
            """
    @coroutine
    def fetch_ssh_login_info(self, params):
        sql = "SELECT s.public_ip, sa.username, sa.passwd FROM server s JOIN server_account sa USING(public_ip) WHERE "
        conds, data = [], []
        if params.get('server_id'):
            conds.append('s.id=%s')
            data.append(params['server_id'])

        if params.get('public_ip'):
            conds.append('s.public_ip=%s')
            data.append(params['public_ip'])

        sql += ' AND '.join(conds)

        cur = yield self.db.execute(sql, data)
        res = cur.fetchone()
        res['passwd'] = Aes.decrypt(res['passwd'])

        return res

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

    def add_image_data(self, params):
        sql = """
                INSERT INTO image (name, version, url, log, app_id, dockerfile, form, lord) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
                ON DUPLICATE key UPDATE log=%s, update_time=NOW(), dockerfile=%s
              """
        arg = [params['name'], params['version'], params['url'], params['log'], params['app_id'], params['dockerfile'],
               params['form'], params['lord'], params['log'], params['dockerfile']]
        self.sync_db_execute(sql, arg)

    def create_image(self, params, out_func=None):
        cmd = CREATE_IMAGE_CMD + ' '.join([params['app_name'], params['image_name'], params['repos_https_url'],
                                           params['branch_name'], params['version']])
        ssh = SSH(hostname=params['public_ip'], port=22, username=params['username'], passwd=params['passwd'])
        out, err = ssh.exec_rt(cmd, out_func)
        return out, err
