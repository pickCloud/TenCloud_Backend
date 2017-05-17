__author__ = 'Jon'

import datetime

from tornado.gen import coroutine
from service.base import BaseService
from constant import CLUSTER_DATE_FORMAT
from utils.general import get_in_format


class ClusterService(BaseService):
    @coroutine
    def get_list(self):
        sql = '''
            SELECT * FROM cluster
        '''

        cur = yield self.db.execute(sql)
        data = cur.fetchall()

        return self._filter_data(data)

    def _filter_data(self, data):
        '''
        :param data: e.g. ((, , , , , datetime.datetime(2017, 5, 16, 10, 27, 27)),)
        :return:     e.g. [{id:, name:, desc:, update_time: '2017年05月16日'},]
        '''
        result = [{
                    'id':   row[0],
                    'name': row[1],
                    'desc': row[2],
                    'update_time': row[5].strftime(CLUSTER_DATE_FORMAT)
                  } for row in data]

        return result

    @coroutine
    def add_cluster(self, params):
        sql = "INSERT INTO cluster (name, description) VALUES (%s, %s)"

        cur = yield self.db.execute(sql, [params['name'], params['desc']])

        return {
            'id': cur.lastrowid,
            'update_time': datetime.datetime.now().strftime(CLUSTER_DATE_FORMAT)
        }

    @coroutine
    def del_cluster(self, params):
        sql = "DELETE FROM cluster WHERE id IN (%s)" % get_in_format(params['id'])

        yield self.db.execute(sql, params['id'])

    @coroutine
    def get_detail(self, params):
        return {}
