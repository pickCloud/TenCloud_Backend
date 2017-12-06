from collections import defaultdict

from tornado.gen import coroutine

from service.base import BaseService
from constant import  PERMISSIONS

class PermissionBaseService(BaseService):

    @coroutine
    def merge_servers(self, data):

        """

        :param [
                  {"a":{"b":[1,2]}},
                  {"a":{"b":[3,4]}},
                  {"c":{"d":[1,2]}},
                ]
        :return: {
                    "a":{
                        "b":[1,2,3,4]
                        }
                    },
                    "c":{
                        "d":[1,2]
                        }
                    }
        """
        res = list()
        result = defaultdict(dict)

        for d in data:
            provider, region = d['provider'], d['region_name']

            if region not in result[provider]:
                result[provider][region] = []

            result[provider][region].append({'id': d['sid'], 'name': d['name']})
        tmp = dict(result.items())
        for k in tmp:
            a_regions = list()
            tmp_provider = {
                'name': k,
                'data': []
            }
            for x in tmp[k]:
                tmp_region = {
                    'name': x,
                    'data': tmp[k][x]
                }
                a_regions.append(tmp_region)
            tmp_provider['data'] = a_regions
            res.append(tmp_provider)
        return res

    @coroutine
    def merge_permissions(self, data):
        res = list()
        result = dict()
        for column in data:
            tmp = {
                'id': column['id'],
                'name': column['name'],
                'group': column['group']
            }
            if column['group'] not in result.keys():
                result[column['group']] = [tmp]
            else:
                result[column['group']].append(tmp)
        for k in result:
            tmp_dict = {
                'name': PERMISSIONS[k],
                'data': [
                    {'name': PERMISSIONS[k], 'data': result[k]}
                ]
            }
            res.append(tmp_dict)
        return res

    @coroutine
    def fetch_instance_info(self, extra=''):
        sql = """
                SELECT i.provider, i.region_name, s.id as sid, s.name FROM instance i 
                JOIN server s USING(instance_id) {extra}
              """.format(extra=extra)
        cur = yield self.db.execute(sql)
        info = cur.fetchall()
        return info
