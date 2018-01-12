__author__ = 'Jon'

import redis
import pymysql.cursors

from tornado_mysql import pools, cursors
from DBUtils.PooledDB import PooledDB

from setting import settings


DB = pools.Pool(
        dict(host=settings['mysql_host'],
             port=settings['mysql_port'],
             user=settings['mysql_user'],
             passwd=settings['mysql_password'],
             db=settings['mysql_database'],
             cursorclass=cursors.DictCursor,
             charset=settings['mysql_charset']),
        max_idle_connections=4,
        max_recycle_sec=120
     )


pool = PooledDB(pymysql, maxcached=1, maxconnections=2,
                host=settings['mysql_host'],
                user=settings['mysql_user'],
                password=settings['mysql_password'],
                db=settings['mysql_database'],
                charset=settings['mysql_charset'],
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True)
SYNC_DB = pool.connection()



REDIS = redis.StrictRedis(host=settings['redis_host'], port=settings['redis_port'], decode_responses=True)