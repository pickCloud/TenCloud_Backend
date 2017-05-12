__author__ = 'Jon'

'''
log文件
    usage::
    >>> from log import LOG
    >>> LOG.debug('test debug')
    >>> LOG.info('test info')
    >>> LOG.warn('test warn')
    >>> LOG.error('test error')
    >>> LOG.stats('test stats')
'''

import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler


# 新增level, 用于统计
logging.addLevelName(60, 'STATS')


class ExactLogLevelFilter(logging.Filter):
    def __init__(self, level):
        self.__level = level

    def filter(self, log_record):
        return log_record.levelno == self.__level


class TenLogService():
    def __init__(self, name='Dashboard',
                       path='logs/',
                       when='D',
                       backcount=7,
                       fmt='[%(levelname)1.1s %(asctime)s %(module)s:%(lineno)d] %(message)s',
                       datefmt='%y%m%d %H:%M:%S',
                       log_level='DEBUG'):
        '''
        :param name:      logger name
        :param path:      目录, 默认当前目录的logs
        :param when:      备份时间, 默认一天备份一次
        :param backcount: 备份数, 默认只备份7个文件, 即只保留一礼拜的log
        :param fmt:       logging.Formatter的fmt, e.g. [W 161212 16:23:47 log:95] message
        :param datefmt:   logging.Formatter的datefmt, e.g. 161212 16:23:47
        :param log_level: 日记级别 e.g. DEBUG
        '''
        self.__logger = logging.getLogger(name)
        self.__logger.setLevel(log_level)

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
            'STATS':    os.path.join(path, 'stats/stats.log')
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

    def stats(self, msg):
        '''用户行为日志, msg可以是dict/list
        '''
        msg = self._wrap_msg(str(msg))

        self.__logger.log(logging.getLevelName('STATS'), msg)

LOG = TenLogService()
