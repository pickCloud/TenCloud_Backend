__author__ = 'Jon'

'''
项目路由文件
'''

from handler.cluster.cluster import ClusterHandler, ClusterDetailHandler, ClusterAllProviders, ClusterSearchHandler
from handler.permission.permission import PermissionTemplateListHandler, PermissionTemplateHandler, \
    PermissionTemplateRenameHandler, PermissionUserDetailHandler, PermissionUserUpdateHandler, \
    PermissionTemplateAddHandler, PermissionResourcesHandler, PermissionTemplateDelHandler, \
    PermissionTemplateUpdateHandler
from handler.project.project import ProjectHandler, ProjectNewHandler, ProjectDelHandler, \
    ProjectDetailHandler, ProjectUpdateHandler, ProjectDeploymentHandler, \
    ProjectImageCreationHandler, ProjectImageFindHandler, ProjectVersionsHandler, \
    ProjectImageLogHandler, ProjectContainersListHanler, ProjectImageUpload, \
    ProjectImageCloudDownload
from handler.repository.repository import RepositoryHandler, RepositoryBranchHandler, GithubOauthCallbackHandler
from handler.server.server import ServerNewHandler, ServerReport, ServerMigrationHandler, ServerDelHandler, \
    ServerDetailHandler, ServerPerformanceHandler, ServerUpdateHandler, \
    ServerStopHandler, ServerStartHandler, ServerRebootHandler, \
    ServerStatusHandler, ServerContainerPerformanceHandler, ServerContainersHandler, \
    ServerContainersInfoHandler, ServerContainerStartHandler, ServerContainerStopHandler, \
    ServerContainerDelHandler, OperationLogHandler
from handler.user.user import UserLoginHandler, UserLogoutHandler, UserSMSHandler, UserDetailHandler, \
                              UserUpdateHandler, UserUploadToken, GetCaptchaHandler, \
                              PasswordLoginHandler, UserRegisterHandler, UserResetPasswordHandler, \
                              UserResetMobileHandler, UserPasswordSetHandler, UserReturnSMSCountHandler, \
                              UserSmsSetHandler, UserDeleteHandler

from handler.file.file import FileUploadHandler, FileUpdateHandler, FileInfoHandler, FileDownloadHandler, \
                                FileDeleteHandler, FileDirCreateHandler, FileListHandler, FileTotalHandler
from handler.company.company import CompanyNewHandler, CompanyUpdateHandler, CompanyEntrySettingHandler, \
                                    CompanyApplicationHandler, CompanyApplicationAcceptHandler, CompanyApplicationRejectHandler, \
                                    CompanyEmployeeHandler, CompanyHandler, CompanyDetailHandler, CompanyEntryUrlHandler, \
                                    CompanyAdminTransferHandler, CompanyEmployeeDismissionHandler, CompanyApplicationDismissionHandler
from handler.message.message import MessageHandler, GetMessageNumHandler


routes = [
    # 集群相关
    (r'/api/clusters', ClusterHandler),
    (r'/api/cluster/(\d+)', ClusterDetailHandler),
    (r'/api/cluster/(\d+)/providers', ClusterAllProviders),
    (r'/api/cluster/search', ClusterSearchHandler),

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

    (r'/api/log/operation', OperationLogHandler),

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
    (r'/api/user/sms', UserSMSHandler),

    # 测试用
    (r'/api/tmp/user/sms/count/(\d+)', UserSmsSetHandler), # 设置短信验证次数
    (r'/api/tmp/user/delete', UserDeleteHandler), # 删除用户

    (r'/api/user/sms/(\d+)/count', UserReturnSMSCountHandler),
    (r'/api/user/token', UserUploadToken),
    (r'/api/user/captcha', GetCaptchaHandler),
    (r'/api/user/register', UserRegisterHandler),
    (r'/api/user/password/reset', UserResetPasswordHandler),
    (r'/api/user/password/set', UserPasswordSetHandler),
    # (r'/api/user/mobile/reset', UserResetMobileHandler),

    (r'/api/permission/resource/(\d+)', PermissionResourcesHandler),
    (r'/api/permission/template/list/(\d+)', PermissionTemplateListHandler),
    (r'/api/permission/template/(\d+)/format/(\d+)', PermissionTemplateHandler),
    (r'/api/permission/template/add', PermissionTemplateAddHandler),
    (r'/api/permission/template/(\d+)/del', PermissionTemplateDelHandler),
    (r'/api/permission/template/(\d+)/update', PermissionTemplateUpdateHandler),
    (r'/api/permission/template/(\d+)/rename', PermissionTemplateRenameHandler),
    (r'/api/permission/(\d+)/user/(\d+)/detail/format/(\d+)', PermissionUserDetailHandler),
    (r'/api/permission/user/update', PermissionUserUpdateHandler),


    # 公司相关
    (r'/api/companies/list/(-?\d+)', CompanyHandler),
    (r'/api/company/(\d+)', CompanyDetailHandler),
    (r'/api/company/new', CompanyNewHandler),
    (r'/api/company/update', CompanyUpdateHandler),
    (r'/api/company/(\d+)/entry/setting', CompanyEntrySettingHandler),
    (r'/api/company/(\d+)/entry/url', CompanyEntryUrlHandler),
    (r'/api/company/application', CompanyApplicationHandler),
    (r'/api/company/application/accept', CompanyApplicationAcceptHandler),
    (r'/api/company/application/reject', CompanyApplicationRejectHandler),
    (r'/api/company/application/dismission', CompanyApplicationDismissionHandler),
    (r'/api/company/(\d+)/employees', CompanyEmployeeHandler),
    (r'/api/company/employee/dismission', CompanyEmployeeDismissionHandler),
    (r'/api/company/admin/transfer', CompanyAdminTransferHandler),

    # 消息
    (r'/api/messages/?(\d*)', MessageHandler),
    (r'/api/messages/count', GetMessageNumHandler),

    # 文件上传
    (r'/api/file/upload', FileUploadHandler),
    (r'/api/file/update', FileUpdateHandler),
    (r'/api/file/list', FileListHandler),
    (r'/api/file/([\w\W]+)/pages', FileTotalHandler),
    (r'/api/file/download/([\w\W]+)', FileDownloadHandler),
    (r'/api/file/delete', FileDeleteHandler),
    (r'/api/file/dir/create', FileDirCreateHandler),
    (r'/api/file/([\w\W]+)', FileInfoHandler),

]
