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
from utils.db import DB


####################################################################
# 命令行解析 python `pwd`/app.py --port=xxxx &
####################################################################
define('port', default=8010, help='启动端口', type=int)

parse_command_line()


class Application(tornado.web.Application):
    def __init__(self):
        super().__init__(routes, **settings)

        self.db = DB
        self.log = LOG
        self.settings = settings


def main():
    try:
        app = Application()
        app.listen(options.port)
        LOG.info('Sever Listen {port}...'.format(port=options.port))
        tornado.ioloop.IOLoop.instance().start()
    except:
        LOG.error(traceback.format_exc())

if __name__ == '__main__':
    main()