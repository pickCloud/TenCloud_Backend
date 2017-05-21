__author__ = 'Jon'

'''
项目路由文件
'''

from handler.cluster.cluster import ClusterHandler, ClusterNewHandler, ClusterDelHandler, \
                                    ClusterDetailHandler, ClusterUpdateHandler
from handler.imagehub.imagehub import ImagehubHandler, ImagehubBySourceHandler, ImagehubByTypeHandler, \
    ImagehubSearchHandler

routes = [
    (r'/api/clusters', ClusterHandler),
    (r'/api/cluster/new', ClusterNewHandler),
    (r'/api/cluster/del', ClusterDelHandler),
    (r'/api/cluster/detail/(\d+)', ClusterDetailHandler),
    (r'/api/cluster/update', ClusterUpdateHandler),
    (r'/api/imagehub', ImagehubHandler),
    (r'/api/imagehub/source', ImagehubBySourceHandler),
    (r'/api/imagehub/type', ImagehubByTypeHandler),
    (r'/api/imagehub/search', ImagehubSearchHandler),
]
