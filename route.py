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
                                  ServerContainerDelHandler, ServerOperationHandler, RealtimeOutputHandler
from handler.project.project import ProjectHandler, ProjectNewHandler, ProjectDelHandler, \
                                    ProjectDetailHandler, ProjectUpdateHandler, ProjectDeploymentHandler, \
                                    ProjectImageCreationHandler, ProjectImageFindHandler, ProjectVersionsHandler, \
                                    ProjectImageLogHandler, ProjectContainersListHanler, ProjectImageUpload, \
                                    ProjectImageCloudDownload
from handler.repository.repository import RepositoryHandler, RepositoryBranchHandler, GithubOauthCallbackHandler
from handler.user.user import UserLoginHandler, UserLogoutHandler, UserSMSHandler, UserDetailHandler, \
                              UserUpdateHandler, UserUploadToken, GetCaptchaHandler, \
                              PasswordLoginHandler, UserRegisterHandler
from handler.file.file import FileUploadHandler, FileUpdateHandler, FileInfoHandler, FileDownloadHandler, \
                                FileDeleteHandler, FileDirCreateHandler, FileListHandler, FileTotalHandler








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
    (r'/api/server/([\w\W]+)/operation', ServerOperationHandler),


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
    (r'/api/project/([\w\W]+)/image/([\w\W]+)/log', ProjectImageLogHandler),
    (r'/api/project/([\w\W]+)/image', ProjectImageFindHandler),
    (r'/api/project/([\w\W]+)/versions', ProjectVersionsHandler),
    (r'/api/project/containers/list', ProjectContainersListHanler),
    (r'/api/project/image/upload', ProjectImageUpload),
    (r'/api/project/image/cloud/download', ProjectImageCloudDownload),

    # 项目相关之仓库
    (r'/api/repos', RepositoryHandler),
    (r'/api/repos/branches', RepositoryBranchHandler),
    (r'/api/github/oauth/callback', GithubOauthCallbackHandler),

    # 用户相关
    (r'/api/user', UserDetailHandler),
    (r'/api/user/update', UserUpdateHandler),
    (r'/api/user/login', UserLoginHandler),
    (r'/api/user/login/password', PasswordLoginHandler),
    (r'/api/user/logout', UserLogoutHandler),
    (r'/api/user/sms/(\d+)', UserSMSHandler),
    (r'/api/user/token', UserUploadToken),
    (r'/api/user/captcha', GetCaptchaHandler),
    (r'/api/user/register', UserRegisterHandler),

    #文件上传
    (r'/api/file/upload', FileUploadHandler),
    (r'/api/file/update', FileUpdateHandler),
    (r'/api/file/list', FileListHandler),
    (r'/api/file/([\w\W]+)/pages', FileTotalHandler),
    (r'/api/file/download/([\w\W]+)', FileDownloadHandler),
    (r'/api/file/delete', FileDeleteHandler),
    (r'/api/file/dir/create', FileDirCreateHandler),
    (r'/api/file/([\w\W]+)', FileInfoHandler),


    # (r'/api/ssh/realtime/output', RealtimeOutputHandler)
]
