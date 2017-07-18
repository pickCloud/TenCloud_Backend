__author__ = 'Jon'

'''
项目路由文件
'''

from handler.cluster.cluster import ClusterHandler, ClusterNewHandler, ClusterDelHandler,\
                                    ClusterDetailHandler, ClusterUpdateHandler
from handler.imagehub.imagehub import ImagehubHandler, ImagehubBySourceHandler, ImagehubByTypeHandler, \
                                      ImagehubSearchHandler
from handler.server.server import ServerNewHandler, ServerReport, ServerMigrationHandler, ServerDelHandler, \
                                  ServerDetailHandler, ServerPerformanceHandler, ServerUpdateHandler, \
                                  ServerStopHandler, ServerStartHandler, ServerRebootHandler, \
                                  ServerStatusHandler, ServerContainerPerformanceHandler, ServerContainersHandler, \
                                  ServerContainersInfoHandler, ServerContainerStartHandler, ServerContainerStopHandler,\
                                  ServerContainerDelHandler
from handler.project.project import ProjectHandler, ProjectNewHandler, ProjectDelHandler, \
                                    ProjectDetailHandler, ProjectUpdateHandler, ProjectDeploymentHandler, \
                                    ProjectImageCreationHandler, ProjectImageFindHandler
from handler.repository.repository import RepositoryHandler, RepositoryBranchHandler







routes = [
    # 集群相关
    (r'/api/clusters', ClusterHandler),
    (r'/api/cluster/new', ClusterNewHandler),
    (r'/api/cluster/del', ClusterDelHandler),
    (r'/api/cluster/(\d+)', ClusterDetailHandler),
    (r'/api/cluster/update', ClusterUpdateHandler),
    (r'/api/imagehub', ImagehubHandler),
    (r'/api/imagehub/source', ImagehubBySourceHandler),
    (r'/api/imagehub/type', ImagehubByTypeHandler),
    (r'/api/imagehub/search', ImagehubSearchHandler),

    # 主机相关
    (r'/api/server/new', ServerNewHandler),
    (r'/api/server/del', ServerDelHandler),
    (r'/api/server/(\d+)', ServerDetailHandler),
    (r'/api/server/update', ServerUpdateHandler),
    (r'/api/server/migration', ServerMigrationHandler),
    (r'/api/server/performance', ServerPerformanceHandler),

    (r'/api/server/stop/(\d+)', ServerStopHandler),
    (r'/api/server/start/(\d+)', ServerStartHandler),
    (r'/api/server/reboot/(\d+)', ServerRebootHandler),
    (r'/api/server/([\w\W]+)/status', ServerStatusHandler),


    (r'/api/server/containers/(\d+)', ServerContainersHandler),
    (r'/api/server/container/performance', ServerContainerPerformanceHandler),
    (r'/api/server/container/start', ServerContainerStartHandler),
    (r'/api/server/container/stop', ServerContainerStopHandler),
    (r'/api/server/container/del', ServerContainerDelHandler),
    (r'/api/server/([\w\W]+)/container/([\w\W]+)', ServerContainersInfoHandler),


    # 主机相关之远程主机上报信息
    (r'/remote/server/report', ServerReport),

    # 项目相关
    (r'/api/projects', ProjectHandler),
    (r'/api/project/new', ProjectNewHandler),
    (r'/api/project/del', ProjectDelHandler),
    (r'/api/project/(\d+)', ProjectDetailHandler),
    (r'/api/project/update', ProjectUpdateHandler),
    (r'/api/project/deployment', ProjectDeploymentHandler),
    (r'/api/project/image/creation', ProjectImageCreationHandler),
    (r'/api/project/image', ProjectImageFindHandler),

    # 项目相关之仓库
    (r'/api/repos', RepositoryHandler),
    (r'/api/repos/branches', RepositoryBranchHandler),
]
