__author__ = 'Zhang'


from tornado.gen import coroutine
from service.base import BaseService


''' FILE BEGIN
    ImagehubService
        Owner = @张煌辉
        Partner = '@Jon'
        Create = 2017-05-17
        Update = 2017-05-18
        #get_list
        #get_by_source
        #get_by_type
END
'''


class ImagehubService(BaseService):
    @coroutine
    def get_list(self):
        '''SPEC BEGIN
            get_list = 取得镜像仓库列表
        END
        '''
        hub_sql = 'SELECT id, name, description FROM imagehub'
        type_sql = 'SELECT id, type_id, name FROM image_types'
        source_sql = 'SELECT id, source_id, name FROM image_sources'

        hub_cur = yield self.db.execute(hub_sql)
        hub_data = hub_cur.fetchall()

        type_cur = yield self.db.execute(type_sql)
        type_data = type_cur.fetchall()

        source_cur = yield self.db.execute(source_sql)
        source_data = source_cur.fetchall()

        data = {
            'image_types': type_data,
            'image_sources': source_data,
            'imagehub': hub_data
        }

        return data

    @coroutine
    def get_by_source(self, source):
        '''SPEC BEGIN
            get_by_source = 通过来源显示镜像仓库列表
        END
        '''
        sql = "SELECT id, name, description FROM imagehub WHERE source = %d" % source

        curl = yield self.db.execute(sql)
        data = curl.fetchall()

        return data

    @coroutine
    def get_by_type(self, type):
        '''SPEC BEGIN
            get_by_source = 通过类型显示镜像仓库列表
        END
        '''
        sql = "SELECT id, name, description FROM imagehub WHERE type = %d" % type

        curl = yield self.db.execute(sql)
        data = curl.fetchall()

        return data
