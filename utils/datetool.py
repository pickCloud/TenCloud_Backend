__author__ = 'Jon'

import time


def seconds_to_human(seconds=None, format='%Y-%m-%d %H:%M:%S'):
    return time.strftime(format, time.localtime(seconds))