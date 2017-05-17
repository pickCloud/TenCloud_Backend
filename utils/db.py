__author__ = 'Jon'

from setting import settings
from tornado_mysql import pools

DB = pools.Pool(
        dict(host=settings['mysql_host'],
             port=settings['mysql_port'],
             user=settings['mysql_user'],
             passwd=settings['mysql_password'],
             db=settings['mysql_database'],
             charset=settings['mysql_charset']),
        max_idle_connections=16,
        max_recycle_sec=120
     )