__author__ = 'Jon'

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

        return self._change_date_format(data)

    def _change_date_format(self, data):
        '''
        :param data: e.g. ((, , , , datetime.datetime(2017, 5, 16, 10, 24, 31), datetime.datetime(2017, 5, 16, 10, 27, 27)),)
        :return:     e.g. ((, , , , '2017年05月16日', '2017年05月16日'),)
        '''
        result = []

        for d in data:
            row = list(d)
            row[4], row[5] = row[4].strftime(CLUSTER_DATE_FORMAT), row[5].strftime(CLUSTER_DATE_FORMAT)
            result.append(row)

        return result

    @coroutine
    def add_cluster(self, params):
        sql = "INSERT INTO cluster (name, description) VALUES (%s, %s)"

        cur = yield self.db.execute(sql, [params['name'], params['desc']])
        id = cur.lastrowid

        return id