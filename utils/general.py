__author__ = 'Jon'

'''
一些平常的工具
'''
import re
import random
from constant import FULL_DATE_FORMAT, USER_AGENTS

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

def validate_ip(ip):
    rule = '\d+\.\d+\.\d+\.\d+'
    match = re.match(rule, ip)

    if not match:
        raise ValueError("不是合法的IP地址")

def choose_user_agent():
    return random.choice(USER_AGENTS)