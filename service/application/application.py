
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
                id, name, description, status, repos_name, 
                repos_ssh_url, repos_https_url, logo_url, labels,
                image_id, lord, form
            """

    @coroutine
    def fetch_with_label(self, params=None, label=None, fields=None, table=None):
        sql = """
            SELECT {fields}, group_concat(l.name order by l.id) as label_name
            FROM {table} a
            LEFT JOIN label as l
            ON find_in_set(l.id, a.labels) 
        """

        # 给每个查询的字段加上a.前缀，并且将时间字段格式化
        field = re.sub('(\w+)', lambda x: 'a.' + x.group(0), fields or self.fields)
        field += ", DATE_FORMAT(a.create_time, '%s') AS create_time " % FULL_DATE_FORMAT_ESCAPE
        field += ", DATE_FORMAT(a.update_time, '%s') AS update_time " % FULL_DATE_FORMAT_ESCAPE

        #
        conds, param = self.make_pair(params)
        if conds:
            sql += " WHERE a." + " AND a.".join(conds)

        if label:
            if conds:
                sql += " AND find_in_set(%s, a.labels) "
            else:
                sql += " WHERE find_in_set(%s, a.labels) "
            param.append(label)

        sql += " GROUP BY a.id "

        cur = yield self.db.execute(sql.format(table=table or self.table, fields=field), param)
        data = cur.fetchall()
        return data

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

    def sync_insert_log(self, params):
        sql = """
                INSERT INTO _image (name, version, log) VALUES (%s, %s, %s) 
                ON DUPLICATE key UPDATE log=%s, update_time=NOW()
              """
        arg = [params['name'], params['version'], params['log'], params['log']]
        self.sync_db_execute(sql, arg)

    def create_image(self, params, out_func=None):
        cmd = CREATE_IMAGE_CMD + ' '.join([params['app_name'], params['image_name'], params['repos_https_url'],
                                           params['branch_name'], params['version']])
        ssh = SSH(hostname=params['public_ip'], port=22, username=params['username'], passwd=params['passwd'])
        out, err = ssh.exec_rt(cmd, out_func)
        return out, err
