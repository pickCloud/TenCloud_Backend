__author__ = 'Jon'

import tornadoredis

from tornado_mysql import pools, cursors
from setting import settings


DB = pools.Pool(
        dict(host=settings['mysql_host'],
             port=settings['mysql_port'],
             user=settings['mysql_user'],
             passwd=settings['mysql_password'],
             db=settings['mysql_database'],
             cursorclass=cursors.DictCursor,
             charset=settings['mysql_charset']),
        max_idle_connections=16,
        max_recycle_sec=120
     )

REDIS = tornadoredis.Client(host=settings['redis_host'], port=settings['redis_port'])
REDIS.connect()
