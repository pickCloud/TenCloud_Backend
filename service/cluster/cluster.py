__author__ = 'Jon'

import datetime

from tornado.gen import coroutine
from service.base import BaseService
from constant import CLUSTER_DATE_FORMAT


class ClusterService(BaseService):
    @coroutine
    def get_list(self):
        sql = '''
            SELECT * FROM cluster
        '''

        cur = yield self.db.execute(sql)
        data = cur.fetchall()

        return self._change_data(data)

    def _change_data(self, data):
        '''
        :param data: e.g. ((, , , , datetime.datetime(2017, 5, 16, 10, 24, 31), datetime.datetime(2017, 5, 16, 10, 27, 27)),)
        :return:     e.g. ((, , , , '2017年05月16日', '2017年05月16日'),)
        '''
        result = []

        for d in data:
            row = dict()
            row['id'] = d[0]
            row['name'] = d[1]
            row['desc'] = d[2]
            row['update_time'] = d[5].strftime(CLUSTER_DATE_FORMAT)
            result.append(row)

        return result

    @coroutine
    def add_cluster(self, params):
        sql = "INSERT INTO cluster (name, description) VALUES (%s, %s)"

        cur = yield self.db.execute(sql, [params['name'], params['desc']])

        return {
            'id': cur.lastrowid,
            'update_time': datetime.datetime.now().strftime(CLUSTER_DATE_FORMAT)
        }