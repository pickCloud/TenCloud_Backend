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
            SELECT id, name, description, DATE_FORMAT(update_time, '%s') AS update_time FROM cluster
        ''' % CLUSTER_DATE_FORMAT

        cur = yield self.db.execute(sql)
        data = cur.fetchall()

        return data

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
