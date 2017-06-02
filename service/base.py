__author__ = 'Jon'

'''
所有service的父类
'''
import json
from tornado.gen import coroutine
from tornado.httputil import url_concat
from tornado.httpclient import AsyncHTTPClient
from concurrent.futures import ThreadPoolExecutor

from utils.db import DB, REDIS
from utils.log import LOG
from constant import CLUSTER_DATE_FORMAT, CLUSTER_DATE_FORMAT_ESCAPE, POOL_COUNT, HTTP_TIMEOUT, ALIYUN_DOMAIN


class BaseService():
    executor = ThreadPoolExecutor(max_workers=POOL_COUNT)

    def __init__(self):
        self.db = DB
        self.redis = REDIS
        self.log = LOG

    @coroutine
    def select(self, fields=None, conds=None, params=None, ct=True, ut=True, df=None, one=False):
        '''
        :param fields 字段名, str类型, 默认为类变量fields, 可传'id, name, ...'
        :param conds  条件, list类型, 可传['id=%s', 'name=%s']
        :param params 条件值, list类型, 对应conds, 可传[1, 'foo']
        :param ct     是否获取创建时间, True/False
        :param ut     是否获取更新时间, True/False
        :param df     创建时间/更新时间的字符串格式, 可传'%Y-%m-%d %H:%M:%S'
        :param one    是否一行, True/False
        Usage::
            >>> self.select(conds=['id=%s'], params=[id], ct=False)

        :return: [{'id': 1, ...}, ...]
        '''
        sql_params = self._create_query(fields=fields, conds=conds, params=params, ct=ct, ut=ut, df=df)
        cur = yield self.db.execute(*sql_params)

        data = cur.fetchone() if one else cur.fetchall()

        return data

    def _create_query(self, fields=None, conds=None, params=None, ct=True, ut=True, df=None):
        '''创建查询语句与参数, 供db.excute执行
           create_time, update_time比较特殊, 默认都有, 不需要时ct=False, ut=False

        :return: sql or [sql, params]
        '''
        sql = "SELECT {fields} ".format(fields=fields or self.fields)

        if df is None:
            df = CLUSTER_DATE_FORMAT_ESCAPE if conds else CLUSTER_DATE_FORMAT

        if ct:
            sql += ", DATE_FORMAT(create_time, '%s') AS create_time" % df

        if ut:
            sql += ", DATE_FORMAT(update_time, '%s') AS update_time " % df

        sql += 'FROM {table} '.format(table=self.table)

        if not conds:
            sql_params = [sql]
        else:
            sql += ' WHERE ' + ' AND '.join(conds)

            sql_params = [sql, params]

        return sql_params

    @coroutine
    def get(self, data=None, timeout=HTTP_TIMEOUT, host=ALIYUN_DOMAIN):
        '''
        如果必要可以添加kwargs, 比如headers
        :param uri:     e.g. /api
        :param data:    e.g. dict(x=1, y=2)
        :param timeout: e.g. 10
        :param infra:   e.g. True
        :param host:    e.g. 'http://host'
        :return:        e.g. {'status': 0, 'message': 'success', 'data': {}}

        Usage::
            host: 默认das, 若要基础服务infra=True
            >>> uri, data = '/api', {'x': 1}
            >>> res = yield self.get(uri, data[, infra=True])
        '''
        if not data: data = {}

        url = url_concat(host, data)

        self.log.debug('GET: {}'.format(url))
        res = yield AsyncHTTPClient().fetch(url, request_timeout=timeout)
        data = json.loads(res.body.decode())
        self.log.debug('GET: {}, RES: {}'.format(url, data))

        return data