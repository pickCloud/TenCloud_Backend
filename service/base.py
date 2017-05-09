__author__ = 'Jon'

'''
所有service的父类
'''
from utils.db import DB
from utils.log import LOG


class BaseService():
    def __init__(self):
        self.db = DB
        self.log = LOG