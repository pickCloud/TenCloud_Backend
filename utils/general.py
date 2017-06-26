__author__ = 'Jon'

'''
一些平常的工具
'''
import re
from constant import CLUSTER_DATE_FORMAT

def get_formats(contents):
    '''
    :param contents: e.g. [1, 2, 3]
    :return: '%s, %s, %s'
    '''
    return ','.join(['%s'] * len(contents))

def get_in_formats(field, contents):
    '''
    :param field: e.g. id
    :param contents: e.g. [1, 2, 3]
    :return: 'id in (%s, %s, %s)'
    '''
    return '{field} in ({formats})'.format(field=field, formats=get_formats(contents))

def change_db_time(data, format=CLUSTER_DATE_FORMAT):
    '''create_time/update_time 从datetime变成str

    :param data:   e.g. [{'update_time': datetime.datetime(2017, 5, 16, 10, 27, 27), ...}, ...] or
                        {'update_time': datetime.datetime(2017, 5, 16, 10, 27, 27), ...}
    :param format: e.g. '%Y年%m月%d日'
    :return: [{'update_time': '2017年05月16日', ...}, ...] or {'update_time': '2017年05月16日', ...}
    '''
    if not isinstance(data, list):
        data = [data]

    for field in ['create_time', 'update_time']:
        for row in data:
            if row.get(field):
                row[field] = row[field].strftime(format)
            else:
                break

def validate_ip(ip):
    rule = '\d+\.\d+\.\d+\.\d+'
    match = re.match(rule, ip)

    if not match:
        raise ValueError("不是合法的IP地址")