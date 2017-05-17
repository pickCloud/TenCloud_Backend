__author__ = 'Zhang'

import datetime

from tornado.gen import coroutine
from service.base import BaseService
from constant import CLUSTER_DATE_FORMAT, IMAGEHUB_DATE_FORMAT


''' FILE BEGIN
    ImagehubService
        #get_list
        #get_by_source
END
'''


class ImagehubService(BaseService):
    @coroutine
    def get_list(self):
        '''SPEC BEGIN
            get_list = 取得镜像仓库列表
        END
        '''
        sql = '''
               SELECT * FROM imagehub
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
            'id': row[0],
            'name': row[1],
            'url': row[2],
            'versions': row[3],
            'description': row[4],
            'source': row[5],
            'type': row[6],
            'comments': row[7],
            'update_time': row[10].strftime(IMAGEHUB_DATE_FORMAT)
        } for row in data]

        return result

    @coroutine
    def get_by_source(self, params):
        '''SPEC BEGIN
            get_by_source = 通过来源显示镜像仓库列表
        END
        '''
        sql = "SELECT * FROM imagehub WHERE source = %s"

        curl = yield self.db.execute(sql, params['source'])
        data = curl.fetchall()

        return self._filter_data(data)