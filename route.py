__author__ = 'Jon'

'''
项目路由文件
'''

from handler.cluster.cluster import ClusterHandler, ClusterNewHandler, ClusterDelHandler, \
                                    ClusterDetailHandler, ClusterUpdateHandler
from handler.server.server import ServerNewHandler, ServerReport, ServerMigratinHandler, ServerDelHandler, \
                                  ServerDetailHandler, ServerPerformanceHandler, ServerUpdateHandler, \
                                  ServerStopHandler, ServerStartHandler, ServerRebootHandler


routes = [
    # 集群相关
    (r'/api/clusters', ClusterHandler),
    (r'/api/cluster/new', ClusterNewHandler),
    (r'/api/cluster/del', ClusterDelHandler),
    (r'/api/cluster/(\d+)', ClusterDetailHandler),
    (r'/api/cluster/update', ClusterUpdateHandler),

    # 主机相关
    (r'/api/server/new', ServerNewHandler),
    (r'/api/server/del', ServerDelHandler),
    (r'/api/server/(\d+)', ServerDetailHandler),
    (r'/api/server/update', ServerUpdateHandler),
    (r'/api/server/migration', ServerMigratinHandler),
    (r'/api/server/performance/(\d+)', ServerPerformanceHandler),

    (r'/api/server/stop/(\d+)', ServerStopHandler),
    (r'/api/server/start/(\d+)', ServerStartHandler),
    (r'/api/server/reboot/(\d+)', ServerRebootHandler),

    # 远程主机上报信息
    (r'/remote/server/report', ServerReport)
]
