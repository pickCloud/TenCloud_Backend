__author__ = 'Jon'

'''
log文件
'''

import os
import sys
import time
import socket
import logging
from logging.handlers import TimedRotatingFileHandler

from tornado.options import options
from setting import settings
from utils.datetool import seconds_to_human


# 新增level, 用于统计
logging.addLevelName(60, 'STATS')


class ExactLogLevelFilter(logging.Filter):
    def __init__(self, level):
        self.__level = level

    def filter(self, log_record):
        return log_record.levelno == self.__level


class Log(object):
    def __init__(self, name='Dashboard',
                       path='logs/',
                       when='D',
                       backcount=7,
                       fmt='[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                       datefmt='%y%m%d %H:%M:%S'):
        '''
        :param name: logger name
        :param path: 目录, 默认当前目录的logs
        :param when: 备份时间, 默认一天备份一次
        :param backcount: 备份数, 默认只备份7个文件, 即只保留一礼拜的log
        :param fmt: logging.Formatter的fmt, e.g. [W 161212 16:23:47 log:95] message
        :param datefmt: logging.Formatter的datefmt, e.g. 161212 16:23:47
        '''
        self.__logger = logging.getLogger(name)
        self.__logger.setLevel(settings['log_level'])

        self._handlers = dict()
        self._backcount = backcount
        self._when = when
        self._fmt = fmt
        self._datefmt = datefmt

        self.log_path = {
            'DEBUG':    os.path.join(path, 'debug/debug.log'),
            'INFO':     os.path.join(path, 'info/info.log'),
            'WARN':     os.path.join(path, 'warn/warn.log'),
            'ERROR':    os.path.join(path, 'error/error.log'),
            'STATS':     os.path.join(path, 'stats/stats.log')
        }
        self._create_handlers()

    def _create_handlers(self):
        '''各个level, 有各自的文件, e.g. debug.log, error.log
        '''
        log_levels = self.log_path.keys()

        for level in log_levels:
            path = os.path.abspath(self.log_path[level])

            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path))

            self._handlers[level] = TimedRotatingFileHandler(path, when=self._when, backupCount=self._backcount)
            self._handlers[level].setFormatter(logging.Formatter(fmt=self._fmt, datefmt=self._datefmt))
            self._handlers[level].addFilter(ExactLogLevelFilter(logging.getLevelName(level)))

            self.__logger.addHandler(self._handlers[level])

    def _wrap_msg(self, msg):
        return '{filename}:{lineno}\t{msg}'.format(filename=sys._getframe().f_back.f_back.f_code.co_filename,
                                                   lineno=sys._getframe().f_back.f_back.f_lineno,
                                                   msg=msg)

    def debug(self, msg):
        msg = self._wrap_msg(msg)

        self.__logger.debug(msg)

    def info(self, msg):
        msg = self._wrap_msg(msg)

        self.__logger.info(msg)

    def warn(self, msg):
        msg = self._wrap_msg(msg)

        self.__logger.warn(msg)

    def error(self, msg):
        msg = self._wrap_msg(msg)

        self.__logger.error(msg)

    def stats(self, _self, extra=None):
        data = {
            'req_time': seconds_to_human(_self._req_time),
            'hostname': socket.gethostname(),
            'appid':    settings['hr_infra_appid'],
            'http_code': _self.get_status(),
            'status_code': 0,
            'opt_time': '%.2f' % ((time.time() - _self._req_time)*1000),
            'res_type': 'json',
            'req_uri':   _self.request.uri,
            'req_type':  _self.request.method,
            'referer':   _self.request.headers.get('Referer'),
            'remote_ip': _self.request.headers.get('X-Real-IP') or _self.request.remote_ip,
            'useragent': _self.request.headers.get('User-Agent'),
            'event': '{handler}-{method}'.format(handler=_self.__module__ + '.' + _self.__class__.__name__, method=_self.request.method)
        }

        if extra:
            data.update(extra)

        msg = self._wrap_msg(str(data))

        self.__logger.log(logging.getLevelName('STATS'), msg)

LOG = Log()

if __name__ == '__main__':
    LOG = Log(path=options.logpath)

    LOG.debug('test debug')
    LOG.info('test info')
    LOG.warn('test warn')
    LOG.error('test error')
    LOG.stats('test stats')