__author__ = 'Jon'

'''
项目路由文件
'''

from handler.cluster.cluster import ClusterHandler, ClusterNewHandler, ClusterDelHandler, \
                                    ClusterDetailHandler, ClusterUpdateHandler
from handler.server.server import ServerNewHandler, ServerReport, ServerMigratinHandler


routes = [
    # 集群相关
    (r'/api/clusters', ClusterHandler),
    (r'/api/cluster/new', ClusterNewHandler),
    (r'/api/cluster/del', ClusterDelHandler),
    (r'/api/cluster/(\d+)', ClusterDetailHandler),
    (r'/api/cluster/update', ClusterUpdateHandler),

    # 主机相关
    (r'/api/server/new', ServerNewHandler),
    (r'/api/server/migration', ServerMigratinHandler),

    # 远程主机上报信息
    (r'/remote/server/report', ServerReport)
]
