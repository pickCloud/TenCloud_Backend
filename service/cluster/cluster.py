__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService


class ClusterService(BaseService):
    @coroutine
    def get_list(self):
        sql = '''
            SELECT * FROM cluster
        '''

        cur = yield self.db.execute(sql)
        data = cur.fetchall()

        return data

    @coroutine
    def add_cluster(self, params):
        sql = "INSERT INTO cluster (name, description) VALUES (%s, %s)"

        cur = yield self.db.execute(sql, [params['name'], params['desc']])
        id = cur.lastrowid

        return id