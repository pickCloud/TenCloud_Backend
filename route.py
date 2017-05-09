__author__ = 'Jon'

'''
项目路由文件
'''

from handler.server.server import ServerHander


routes = [
    (r'/server/status', ServerHander)
]