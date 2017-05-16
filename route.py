__author__ = 'Jon'

'''
项目路由文件
'''

from handler.cluster.cluster import ClusterHandler, ClusterNewHandler


routes = [
    (r'/api/clusters', ClusterHandler),
    (r'/api/cluster/new', ClusterNewHandler)
]