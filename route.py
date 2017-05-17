__author__ = 'Jon'

'''
项目路由文件
'''

from handler.cluster.cluster import ClusterHandler, ClusterNewHandler, ClusterDelHandler, ClusterDetailHandler
from handler.imagehub.imagehub import ImagehubHandler, ImagehubBySourceHandler


routes = [
    (r'/api/clusters', ClusterHandler),
    (r'/api/cluster/new', ClusterNewHandler),
    (r'/api/cluster/del', ClusterDelHandler),
    (r'/api/cluster/detail', ClusterDetailHandler),
    (r'/api/imagehub', ImagehubHandler),
    (r'/api/imagehub/source', ImagehubBySourceHandler),
]