from collections import defaultdict

from tornado.gen import coroutine

from service.base import BaseService


class PermissionBaseService(BaseService):

    @coroutine
    def merge_dict(self, data):

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
        result = defaultdict(dict)

        for d in data:
            provider, region = d['provider'], d['region_name']

            if region not in result[provider]:
                result[provider][region] = []

            result[provider][region].append({'sid': d['sid'], 'name': d['name']})
        return dict(result.items())

    @coroutine
    def fetch_instance_info(self, extra=''):
        # WHERE s.id in {ids}
        sql = """
                SELECT i.provider, i.region_name, s.id as sid, s.name FROM instance i 
                JOIN server s USING(instance_id) {extra}
              """.format(extra=extra)
        cur = yield self.db.execute(sql)
        info = cur.fetchall()
        return info
