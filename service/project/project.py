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
                     LOAD_IMAGE, CLOUD_DOWNLOAD_IMAGE, YE_PORTMAP
from setting import settings


class ProjectService(BaseService):
    table = 'project'
    fields = """
                id, name, description, repos_name, 
                repos_url, http_url, image_name, mode, status, 
                deploy_ips, container_name, image_source, lord, form
            """

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
        return out, err

    def deployment(self, params, out_func=None):
        image_name = REPOS_DOMAIN + "/library/" + params['image_name']
        cmd = DEPLOY_CMD.format(
            repository=REPOS_DOMAIN,
            username=settings['deploy_username'],
            password=settings['deploy_password'],
            portmap=YE_PORTMAP,
            image_name=image_name,
            container_name=params['container_name'])
        has_err = False
        log = dict()
        for ip in params['infos']:
            ssh = SSH(hostname=ip['public_ip'], port=22, username=ip['username'], passwd=ip['passwd'])
            result = '成功'

            out, err = ssh.exec_rt(cmd, out_func)
            if err:
                has_err, result = True, '失败'

            out_func('IP: {}, 部署{}'.format(ip['public_ip'], result))
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
        params['cmd'] = IMAGE_INFO_CMD % (params['prj_name'])
        out, err = yield self.remote_ssh(params)
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
        params['cmd'] = LIST_CONTAINERS_CMD+sufix
        out, err = yield self.remote_ssh(params)

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

    @coroutine
    def fetch(self, params, fields=None):
        '''
        通过关联project表和user_access_project表，查询用户能访问的项目数据
        :param params: 判断条件，是在表user_access_project上的
        :param fields: 需要查询的表project的字段
        :return:
        '''
        sql = """
            SELECT {fields} FROM project AS a 
            """

        conds, param = self.make_pair(params)
        if params.get('cid'):
            # 因为联表操作，先为每个fields中的字段添加上'a.'
            fields = re.sub('(\w+)', lambda x: 'a.'+x.group(0), fields or self.fields)
            sql += " JOIN user_access_project AS b ON a.id=b.pid "

            sql += ' WHERE b.' + ' AND b.'.join(conds)
        else:
            # 使用form和lord查询属于个人用户的项目
            conds, param = self.make_pair(params)
            sql += ' WHERE ' + ' AND '.join(conds)

        cur = yield self.db.execute(sql.format(fields=fields or self.fields), param)
        data = cur.fetchall()
        return data



