__author__ = 'Jon'

'''
一些平常的工具
'''
import re
import random
import string
import json
from hashlib import md5
from constant import USER_AGENTS

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

def _validate(regex, value, err_msg):
    pattern = re.compile(regex)

    if not pattern.match(value):
        raise ValueError(err_msg)

def validate_ip(ip):
    regex = '\d+\.\d+\.\d+\.\d+'

    _validate(regex, ip, '不是合法的IP地址')

def validate_mobile(mobile):
    regex = r'^1\d{10}$'

    _validate(regex, mobile, '请输入11位手机号')

def validate_auth_code(auth_code):
    regex = r'\d{4}'

    _validate(regex, auth_code, '请输入4位验证码')

def validate_user_password(password):
    regex = r'[\d|\w]{6,20}'

    _validate(regex, password,'密码长度要求6到20位，由大小写字母和数字组成')

def gen_random_code(length=6):
    return ''.join(random.sample('123456789', length))

def choose_user_agent():
    return random.choice(USER_AGENTS)

def json_loads(data):
    ''' json can loads None '''
    return json.loads(data) if data else {}

def json_dumps(data):
    ''' json can dumps None '''
    return json.dumps(data) if data else '{}'

def gen_md5(fp):
    m = md5()
    m.update(fp)

    return m.hexdigest()

def fuzzyfinder(user_input, sourece):
    """
    :param user_input str:
    :param sourece []int:
    :return:
    """
    suggestions = []
    pattern = '.*?'.join(user_input)  # Converts 'djm' to 'd.*?j.*?m'
    regex = re.compile(pattern)  # Compiles a regex.
    for item in sourece:
        match = regex.search(item)  # Checks if the current item matches the regex.
        if match:
            suggestions.append((len(match.group()), match.start(), item))
    return [x for _, _, x in sorted(suggestions)]
