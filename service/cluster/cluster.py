__author__ = 'Jon'

import datetime

from tornado.gen import coroutine
from service.base import BaseService
from constant import CLUSTER_DATE_FORMAT
from utils.general import get_in_format


class ClusterService(BaseService):
    table  = 'cluster'
    fields = 'id, name, description'

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
    def update_cluster(self, params):
        sql = "UPDATE cluster SET name=%s, description=%s WHERE id=%s"

        yield self.db.execute(sql, [params['name'], params['desc'], params['id']])