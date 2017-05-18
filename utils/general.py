__author__ = 'Jon'

'''
一些平常的工具
'''
from constant import CLUSTER_DATE_FORMAT

def get_in_format(contens):
    '''
    :param contens: e.g. [1, 2, 3]
    :return: '%s, %s, %s'
    '''
    return ','.join(['%s'] * len(contens))


def change_update_time(data, format=CLUSTER_DATE_FORMAT):
    '''
    :param data:   e.g. [{'update_time': datetime.datetime(2017, 5, 16, 10, 27, 27), ...}, ...] or
                        {'update_time': datetime.datetime(2017, 5, 16, 10, 27, 27), ...}
    :param format: e.g. '%Y年%m月%d日'
    :return: [{'update_time': '2017年05月16日', ...}, ...] or {'update_time': '2017年05月16日', ...}
    '''
    if not isinstance(data, list):
        data = [data]

    for row in data:
        if row.get('update_time'):
            row['update_time'] = row['update_time'].strftime(format)