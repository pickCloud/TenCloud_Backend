__author__ = 'Jon'

'''
所有service的父类

说明
---------------
* DB的增/删/查/改 (复杂的需要手写sql语句)
* HTTP的异步请求

'''
import json
import re
import datetime
from tornado.gen import coroutine
from tornado.httputil import url_concat, HTTPHeaders
from tornado.httpclient import AsyncHTTPClient, HTTPError
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

from utils.db import DB, REDIS, SYNC_DB
from utils.log import LOG
from utils.ssh import SSH
from utils.general import get_formats, get_in_formats, get_not_in_formats, choose_user_agent
from constant import FULL_DATE_FORMAT, FULL_DATE_FORMAT_ESCAPE, POOL_COUNT, HTTP_TIMEOUT, ALIYUN_DOMAIN, NEG, \
                     DEFAULT_PAGE_NUM, MAX_PAGE_NUMBER


class BaseService():
    executor = ThreadPoolExecutor(max_workers=POOL_COUNT)

    def __init__(self):
        self.db = DB
        self.sync_db = SYNC_DB
        self.redis = REDIS
        self.log = LOG

    ############################################################################################
    # DB SELECT
    ############################################################################################
    @coroutine
    def select(self, conds=None, fields=None, ct=True, ut=True, df=None, one=False, extra='', page=None,
               num=DEFAULT_PAGE_NUM):
        '''
        :param fields 字段名, str类型, 默认为类变量fields, 可传'id, name, ...'
        :param conds  条件, dict类型, 可传{'name': 'foo'}/{'name~': 'foo'} or {'age': [10, 20]}/{'age~': [10, 20]}
        :param ct     是否获取创建时间, True/False
        :param ut     是否获取更新时间, True/False
        :param df     创建时间/更新时间的字符串格式, 可传'%Y-%m-%d %H:%M:%S'
        :param one    是否一行, True/False
        :param extra   额外
        :param page   页数
        :param num    每页消息数

        Usage::
            >>> self.select(conds={'id': 1}, ct=False)

        :return: [{'id': 1, ...}, ...]
        '''
        conds, params = self.make_pair(conds)

        sql_params = self._create_query(fields=fields, conds=conds, params=params, ct=ct, ut=ut, df=df, extra=extra,
                                        page=page, num=num)
        cur = yield self.db.execute(*sql_params)

        data = cur.fetchone() if one else cur.fetchall()

        return data

    def _create_query(self, fields=None, conds=None, params=None, ct=True, ut=True, df=None, extra='', page=None,
                      num=DEFAULT_PAGE_NUM):
        '''创建查询语句与参数, 供db.excute执行
           create_time, update_time比较特殊, 默认都有, 不需要时ct=False, ut=False

        :return: sql or [sql, params]
        '''
        sql = "SELECT {fields} ".format(fields=fields or self.fields)

        if df is None:
            df = FULL_DATE_FORMAT_ESCAPE if conds else FULL_DATE_FORMAT

        if ct:
            sql += ", DATE_FORMAT(create_time, '%s') AS create_time" % df

        if ut:
            sql += ", DATE_FORMAT(update_time, '%s') AS update_time " % df

        sql += 'FROM {table} '.format(table=self.table)

        if page:
            page_num = int(num) if 0 < int(num) < MAX_PAGE_NUMBER else DEFAULT_PAGE_NUM
            extra += ' LIMIT {},{} '.format((int(page)-1)*page_num, page_num)

        if not conds:
            sql_params = [sql+extra]
        else:
            sql += ' WHERE ' + ' AND '.join(conds)
            sql_params = [sql+extra, params]

        return sql_params

    ############################################################################################
    # DB ADD
    ############################################################################################
    @coroutine
    def add(self, params=None):
        '''
        :param params: hash 数据库字段:值, 可传{'name': 'foo', 'description': 'boo'}
        :return: {
            'id': cur.lastrowid,
            'update_time': datetime.datetime.now().strftime(FULL_DATE_FORMAT)
        }
        '''
        fields = ','.join(params.keys())
        values = list(params.values())

        sql = """
                INSERT INTO {table} ({fields}) VALUES ({formats})
                ON DUPLICATE KEY UPDATE update_time=NOW()
              """.format(table=self.table, fields=fields, formats=get_formats(values))

        cur = yield self.db.execute(sql, values)

        return {
            'id': cur.lastrowid,
            'update_time': datetime.datetime.now().strftime(FULL_DATE_FORMAT)
        }

    ############################################################################################
    # DB UPDATE
    ############################################################################################
    @coroutine
    def update(self, sets=None, conds=None):
        '''
        :param sets:   dict e.g. {'name': 'foo', 'description': 'boo'}
        :param conds:  dict 同select
        '''
        sets, s_params = self.make_pair(sets)
        conds, c_params = self.make_pair(conds)

        sql = "UPDATE {table} SET ".format(table=self.table)

        sql += ','.join(sets)

        sql += ' WHERE ' + ' AND '.join(conds)

        yield self.db.execute(sql, s_params + c_params)

    ############################################################################################
    # DB DELETE
    ############################################################################################
    @coroutine
    def delete(self, conds=None):
        '''
        :param conds:  dict 同select 必需的
        '''
        conds, params = self.make_pair(conds)

        sql = " DELETE FROM {table} ".format(table=self.table)

        sql += ' WHERE ' + ' AND '.join(conds)

        yield self.db.execute(sql, params)

    ############################################################################################
    # DB SQL TOOLS
    ############################################################################################
    def _has_neg(self, s):
        ''' 如果s尾部有NEG，则去掉, 并且返回True
        :param s: name or name~
        :return: False, name or True name
        '''
        if s[-1] == NEG:
            return True, s[:-1]

        return False, s

    def make_pair(self, args=None):
        ''' 根据args生成conds, params
        :param args: {'name': 'foo', 'age': [20, 30]}
        :return ['name=%s', 'status in (%s, %s)'], ['foo', 20, 30]
        '''
        if args is None: args = {}

        conds, params = [], []

        for k, v in args.items():
            if isinstance(v, list):
                flag, k = self._has_neg(k)
                c = get_not_in_formats(k, v) if flag else get_in_formats(k, v)
                conds.append(c)
                params.extend(v)
            else:
                flag, k = self._has_neg(k)
                c = k + '!=%s' if flag else k + '=%s'
                conds.append(c)
                params.append(v)

        return conds, params

    ############################################################################################
    # HTTP GET
    ############################################################################################
    @coroutine
    def get(self, data=None, host=ALIYUN_DOMAIN, timeout=HTTP_TIMEOUT, headers=None):
        '''
        如果必要可以添加kwargs, 比如headers
        :param data:    dict e.g. dict(x=1, y=2)
        :param host:    str  e.g. 'http://host'
        :param timeout: int  e.g. 10
        :param headers: dict e.g. dict(Authorization='')
        :return:        e.g. {'status': 0, 'message': 'success', 'data': {}}

        Usage::
            >>> uri, data = '/api', {'x': 1}
            >>> res = yield self.get(uri, data)
        '''
        url = url_concat(host, data)

        payload = {
            'request_timeout': timeout,
            'headers': {'User-Agent': choose_user_agent()}
        }

        if headers:
            payload['headers'].update(headers)

        payload['headers'] = HTTPHeaders(payload['headers'])

        try:
            res = yield AsyncHTTPClient().fetch(url, **payload)
        except HTTPError as e:
            err = 'STATUS: {status}, BODY: {body}, URL: {url}'.format(status=str(e), body=e.response.body, url=e.response.effective_url)
            raise ValueError(err)

        body = json.loads(res.body.decode())

        return body

    @coroutine
    def post(self, url, data=None, headers=None, timeout=HTTP_TIMEOUT):
        if not data: data = {}

        if not headers:
            headers = {
                'User-Agent': choose_user_agent(),
                'Accept': 'application/json'
            }

        try:
            res = yield AsyncHTTPClient().fetch(url,
                                                method='POST',
                                                body=urlencode(data),
                                                headers=HTTPHeaders(headers),
                                                request_timeout=timeout)
        except HTTPError as e:
            err = 'STATUS: {status}, BODY: {body}, URL: {url}'.format(status=str(e), body=e.response.body, url=e.response.effective_url)
            raise ValueError(err)

        body = json.loads(res.body.decode())

        return body


    ############################################################################################
    # SSH
    ############################################################################################
    @run_on_executor
    def remote_ssh(self, params):
        """ 远程控制主机
        :param params: dict, 必须{'public_ip', 'username', 'passwd', 'cmd'}, 可选{'rt'(实时输出), 'out_func'}
        """
        try:
            ssh = SSH(hostname=params['public_ip'], username=params['username'], passwd=params['passwd'])

            if params.get('rt'):
                out, err = ssh.exec_rt(params['cmd'], params.get('out_func'))
            else:
                out, err = ssh.exec(params['cmd'])
            ssh.close()

            return out, err
        except Exception as e:
            return [], [str(e)]

    def sync_db_execute(self, sql, params):
        cur = self.sync_db.cursor()
        cur.execute(sql, params)
        index = cur.lastrowid
        cur.close()
        return index

    def sync_db_fetchone(self, sql, params):
        cur = self.sync_db.cursor()
        cur.execute(sql, params)
        res = cur.fetchone()
        cur.close()

        return res

    def sync_db_fetchall(self, sql, params):
        cur = self.sync_db.cursor()
        cur.execute(sql, params)
        res = cur.fetchall()
        cur.close()

        return res

    def sync_update(self, sets=None, conds=None, table=None):
        '''
        :param sets:   dict e.g. {'name': 'foo', 'description': 'boo'}
        :param conds:  dict 同select
        '''
        sets, s_params = self.make_pair(sets)
        conds, c_params = self.make_pair(conds)

        sql = "UPDATE {table} SET ".format(table=table or self.table)

        sql += ','.join(sets)

        sql += ' WHERE ' + ' AND '.join(conds)

        self.sync_db_execute(sql, s_params + c_params)

    def sync_select(self, conds=None, fields=None, ct=True, ut=True, df=None, one=False, extra='', page=None,
                    num=DEFAULT_PAGE_NUM):
        '''
        :param fields 字段名, str类型, 默认为类变量fields, 可传'id, name, ...'
        :param conds  条件, dict类型, 可传{'name': 'foo'}/{'name~': 'foo'} or {'age': [10, 20]}/{'age~': [10, 20]}
        :param ct     是否获取创建时间, True/False
        :param ut     是否获取更新时间, True/False
        :param df     创建时间/更新时间的字符串格式, 可传'%Y-%m-%d %H:%M:%S'
        :param one    是否一行, True/False
        :param extra   额外
        :param page   页数
        :param num    每页消息数

        Usage::
            >>> self.select(conds={'id': 1}, ct=False)

        :return: [{'id': 1, ...}, ...]
        '''
        conds, params = self.make_pair(conds)

        sql_params = self._create_query(fields=fields, conds=conds, params=params, ct=ct, ut=ut, df=df, extra=extra,
                                        page=page, num=num)
        cur = self.sync_db.cursor()
        cur.execute(*sql_params)

        data = cur.fetchone() if one else cur.fetchall()

        return data

    def sync_add(self, params=None):
        '''
        :param params: hash 数据库字段:值, 可传{'name': 'foo', 'description': 'boo'}
        :return: {
            'id': cur.lastrowid,
            'update_time': datetime.datetime.now().strftime(FULL_DATE_FORMAT)
        }
        '''
        fields = ','.join(params.keys())
        values = list(params.values())
        sets, sets_params = self.make_pair(params)

        sql = """
                INSERT INTO {table} ({fields}) VALUES ({formats})
                ON DUPLICATE KEY UPDATE update_time=NOW()
              """.format(table=self.table, fields=fields, formats=get_formats(values))
        sql += ',' + ','.join(sets)

        index = self.sync_db_execute(sql, values + values)
        return index

    def sync_delete(self, conds=None):
        '''
        :param conds:  dict 同select 必需的
        '''
        conds, params = self.make_pair(conds)

        sql = " DELETE FROM {table} ".format(table=self.table)

        sql += ' WHERE ' + ' AND '.join(conds)

        self.sync_db_execute(sql, params)


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

    @coroutine
    def add_k8s_resource(self, params=None):
        '''
        :param params: hash 数据库字段:值, 可传{'name': 'foo', 'description': 'boo'}
        :return: {
            'id': cur.lastrowid,
            'update_time': datetime.datetime.now().strftime(FULL_DATE_FORMAT)
        }
        '''
        fields = ','.join(params.keys())
        values = list(params.values())

        sql = """
                    INSERT INTO {table} ({fields}) VALUES ({formats})
                    ON DUPLICATE KEY UPDATE update_time=NOW(),verbose=%s
                  """.format(table=self.table, fields=fields, formats=get_formats(values))

        cur = yield self.db.execute(sql, values, params.get('verbose', ''))

        return {
            'id': cur.lastrowid,
            'update_time': datetime.datetime.now().strftime(FULL_DATE_FORMAT)
        }