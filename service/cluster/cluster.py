__author__ = 'Jon'

from tornado.gen import coroutine

from service.base import BaseService
from utils.general import fuzzyfinder


class ClusterService(BaseService):
    table  = 'cluster'
    fields = 'id, name, description, status'

    @coroutine
    def select_by_name(self, data, server_name):
        names = []
        sorted_data = dict()
        for i in data:
            key = i['name']
            sorted_data[key] = i
            names.append(key)

        name_find = fuzzyfinder(server_name, names)
        final_data = [sorted_data[key] for key in names if key in name_find]
        return final_data

    @coroutine
    def get_all_providers(self, cluster_id):
        sql = """
            SELECT i.provider, i.region_name FROM instance as i 
            LEFT JOIN server as s ON s.public_ip=i.public_ip
            WHERE s.cluster_id=%s
            ORDER BY i.provider
            """
        cur = yield self.db.execute(sql, [cluster_id])
        data = [dict(t) for t in set([tuple(d.items()) for d in cur.fetchall()])]
        result = dict()
        res = []
        for i in data:
            result.setdefault(i['provider'], []).append(i['region_name'])

        for k in result:
            tmp = {
                'provider': k,
                'regions': result[k]
            }
            res.append(tmp)
        return res