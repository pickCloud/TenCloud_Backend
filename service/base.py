__author__ = 'Jon'

'''
所有service的父类
'''

from tornado.gen import coroutine

from utils.db import DB, REDIS
from utils.log import LOG
from constant import CLUSTER_DATE_FORMAT


class BaseService():
    def __init__(self):
        self.db = DB
        self.redis = REDIS
        self.log = LOG

    @coroutine
    def select(self, conds=None, params=None, ct=True, ut=True, df=CLUSTER_DATE_FORMAT):
        '''
        :return: [{'id': 1, ...}, ...]
        '''
        sql_params = self.create_query(conds=conds, params=params, ct=ct, ut=ut, df=df)
        cur = yield self.db.execute(*sql_params)

        data = cur.fetchall()

        return data

    def create_query(self, fields=None, table=None, conds=None, params=None, ct=True, ut=True, df=CLUSTER_DATE_FORMAT):
        '''
            创建查询语句与参数, 供db.excute执行
            create_time, update_time比较特殊, 默认都有, 不需要时ct=False, ut=False

        :param fields: e.g. 'id, name'
        :param table:  e.g. 'cluster'
        :param conds:  e.g. ['id=%s', 'name=%s']
        :param params: e.g. [1, 'x']
        :param df:     e.g. '%%Y-%%m-%%d'
        :return: sql or [sql, params]
        '''
        sql = "SELECT {fields} ".format(fields=fields or self.fields)

        if ct:
            sql += ", DATE_FORMAT(create_time, '%s') AS create_time" % df

        if ut:
            sql += ", DATE_FORMAT(update_time, '%s') AS update_time " % df

        sql += 'FROM {table} '.format(table=table or self.table)

        if not conds:
            sql_params = [sql]
        else:
            sql += ' WHERE ' + ' AND '.join(conds)

            sql_params = [sql, params]

        return sql_params

