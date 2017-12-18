__author__ = 'Jon'

'''
项目启动文件
'''
import traceback
import tornado.ioloop
import tornado.web

from tornado.options import options, define, parse_command_line
from route import routes
from setting import settings
from utils.log import LOG
from utils.db import DB, REDIS
from constant import TORNADO_MAX_BODY_SIZE


####################################################################
# 命令行解析 python `pwd`/app.py --port=xxxx &
####################################################################
define('port', default=8010, help='启动端口', type=int)
define('address', default='127.0.0.1', help='监听ip', type=str)

parse_command_line()


class Application(tornado.web.Application):
    def __init__(self):
        super().__init__(routes, **settings)

        self.db = DB
        self.log = LOG
        self.redis = REDIS
        self.settings = settings


def main():
    try:
        app = Application()
        app.listen(address=options.address, port=options.port, max_body_size=TORNADO_MAX_BODY_SIZE)
        LOG.info('Sever Listen {port}...'.format(port=options.port))
        tornado.ioloop.IOLoop.instance().start()
    except:
        LOG.error(traceback.format_exc())

if __name__ == '__main__':
    main()
