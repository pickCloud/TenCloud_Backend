__author__ = 'Jon'

'''
项目路由文件
'''

from handler.cluster.cluster import ClusterHandler, ClusterDetailHandler, ClusterAllProviders, ClusterSearchHandler, \
    ClusterWarnServerHandler, ClusterSummaryHandler, ClusterNodeListHandler, ClusterNewHandler
from handler.permission.permission import PermissionTemplateListHandler, PermissionTemplateHandler, \
    PermissionTemplateRenameHandler, PermissionUserDetailHandler, PermissionUserUpdateHandler, \
    PermissionTemplateAddHandler, PermissionResourcesHandler, PermissionTemplateDelHandler, \
    PermissionTemplateUpdateHandler
from handler.application.application import ApplicationNewHandler, ApplicationDeleteHandler, ApplicationBriefHandler, \
                                            ApplicationSummaryHandler, ApplicationUpdateHandler, ImageCreationHandler, \
                                            SubApplicationBriefHandler
from handler.imagehub.image import ImageDetailHandler, ImageNewHandler
from handler.application.deployment import K8sDeploymentHandler, K8sDeploymentNameCheckHandler, DeploymentBriefHandler, \
                                           K8sDeploymentYamlGenerateHandler, DeploymentReplicasSetSourceHandler, \
                                           DeploymentPodSourceHandler, DeploymentLastestHandler, \
                                           ApplicationPodLabelsHandler, DeploymentDeleteHandler
from handler.application.service import K8sServiceYamlGenerateHandler, ServiceBriefHandler, ServiceDetailHandler, \
                                        K8sServiceHandler, ServiceDeleteHandler, IngressInfolHandler, \
                                        IngressConfigHandler, ServicePortListHandler
from handler.label.label import LabelListHandler, LabelAddHandler, LabelDelHandler
from handler.project.project import ProjectHandler, ProjectNewHandler, ProjectDelHandler, \
    ProjectDetailHandler, ProjectUpdateHandler, ProjectDeploymentHandler, \
    ProjectImageCreationHandler, ProjectImageFindHandler, ProjectVersionsHandler, \
    ProjectImageLogHandler, ProjectContainersListHanler, ProjectImageUpload, \
    ProjectImageCloudDownload
from handler.repository.repository import RepositoryHandler, RepositoryBranchHandler, GithubOauthCallbackHandler, \
    GithubOauthClearHandle
from handler.server.server import ServerNewHandler, ServerReport, ServerDelHandler, \
    ServerDetailHandler, ServerPerformanceHandler, ServerUpdateHandler, \
    ServerStopHandler, ServerStartHandler, ServerRebootHandler, \
    ServerStatusHandler, ServerContainerPerformanceHandler, ServerContainersHandler, \
    ServerContainersInfoHandler, ServerContainerStartHandler, ServerContainerStopHandler, \
    ServerContainerDelHandler, OperationLogHandler, SystemLoadHandler, ServerThresholdHandler,ServerMontiorHandler
from handler.cloud.cloud import CloudsHandler, CloudCredentialHandler
from handler.user.user import UserLoginHandler, UserLogoutHandler, UserSMSHandler, UserDetailHandler, \
                              UserUpdateHandler, UserUploadToken, GetCaptchaHandler, \
                              PasswordLoginHandler, UserRegisterHandler, UserResetPasswordHandler, \
                              UserPasswordSetHandler, UserReturnSMSCountHandler, \
                              UserSmsSetHandler, UserDeleteHandler

from handler.file.file import FileUploadHandler, FileUpdateHandler, FileInfoHandler, FileDownloadHandler, \
                              FileDeleteHandler, FileDirCreateHandler, FileListHandler, FileTotalHandler, \
                              FileDownloadPreHandler
from handler.company.company import CompanyNewHandler, CompanyUpdateHandler, CompanyEntrySettingHandler, \
                                    CompanyApplicationHandler, CompanyApplicationAcceptHandler, CompanyApplicationRejectHandler, \
                                    CompanyEmployeeHandler, CompanyHandler, CompanyDetailHandler, CompanyEntryUrlHandler, \
                                    CompanyAdminTransferHandler, CompanyEmployeeDismissionHandler, CompanyApplicationDismissionHandler, \
                                    CompanyApplicationWaitingHandler, ComapnyEmployeeSearchHandler, \
                                    CompanyEmployeeStatusHandler
from handler.message.message import MessageHandler, MessageCountHandler, MessageSearchHandler


routes = [
    # 集群相关
    (r'/api/clusters', ClusterHandler),
    (r'/api/cluster/(\d+)', ClusterDetailHandler),
    (r'/api/cluster/(\d+)/providers', ClusterAllProviders),
    (r'/api/cluster/search', ClusterSearchHandler),
    (r'/api/cluster/warn/(\d+)', ClusterWarnServerHandler),
    (r'/api/cluster/summary', ClusterSummaryHandler),
    (r'/api/cluster/node', ClusterNodeListHandler),
    (r'/api/cluster/new', ClusterNewHandler),

    # 主机相关
    (r'/api/server/new', ServerNewHandler),
    (r'/api/server/del', ServerDelHandler),
    (r'/api/server/threshold', ServerThresholdHandler),
    (r'/api/server/(\d+)', ServerDetailHandler),
    (r'/api/server/update', ServerUpdateHandler),
    (r'/api/server/performance', ServerPerformanceHandler),
    (r'/api/server/(\d+)/systemload', SystemLoadHandler),
    (r'/api/server/monitor', ServerMontiorHandler),

    (r'/api/clouds', CloudsHandler),
    (r'/api/clouds/credentials', CloudCredentialHandler),

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
    (r'/api/github/clear', GithubOauthClearHandle),

    # 构建相关
    (r'/api/build', ImageCreationHandler),

    # 部署相关
    (r'/api/k8s_deploy', K8sDeploymentHandler),
    (r'/api/deployment/check_name', K8sDeploymentNameCheckHandler),
    (r'/api/deployment/generate', K8sDeploymentYamlGenerateHandler),
    (r'/api/deployment/brief', DeploymentBriefHandler),
    (r'/api/deployment/latest', DeploymentLastestHandler),
    (r'/api/deployment/replicas', DeploymentReplicasSetSourceHandler),
    (r'/api/deployment/pods', DeploymentPodSourceHandler),
    (r'/api/deployment/delete', DeploymentDeleteHandler),

    # service相关
    (r'/api/service/generate', K8sServiceYamlGenerateHandler),
    (r'/api/service/brief', ServiceBriefHandler),
    (r'/api/service/detail', ServiceDetailHandler),
    (r'/api/k8s_service', K8sServiceHandler),
    (r'/api/service/delete', ServiceDeleteHandler),
    (r'/api/ingress/info', IngressInfolHandler),
    (r'/api/ingress/config', IngressConfigHandler),
    (r'/api/service/service_port', ServicePortListHandler),

    # 镜像相关
    (r'/api/image', ImageDetailHandler),
    (r'/api/image/new', ImageNewHandler),

    # 应用相关
    (r'/api/application/new', ApplicationNewHandler),
    (r'/api/application/del', ApplicationDeleteHandler),
    (r'/api/application/update', ApplicationUpdateHandler),
    (r'/api/application/brief', ApplicationBriefHandler),
    (r'/api/application/summary', ApplicationSummaryHandler),
    (r'/api/sub_application/brief', SubApplicationBriefHandler),
    (r'/api/application/pod_labels', ApplicationPodLabelsHandler),

    # 标签相关
    (r'/api/label/new', LabelAddHandler),
    (r'/api/label/list', LabelListHandler),
    (r'/api/label/del', LabelDelHandler),

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
    (r'/api/company/application/waiting', CompanyApplicationWaitingHandler),
    (r'/api/company/(\d+)/employees', CompanyEmployeeHandler),
    (r'/api/company/employee/dismission', CompanyEmployeeDismissionHandler),
    (r'/api/company/admin/transfer', CompanyAdminTransferHandler),
    (r'/api/company/employee/search', ComapnyEmployeeSearchHandler),
    (r'/api/company/employee/status', CompanyEmployeeStatusHandler),

    # 消息
    (r'/api/messages/?(\d*)', MessageHandler),
    (r'/api/messages/count', MessageCountHandler),
    (r'/api/messages/search', MessageSearchHandler),

    # 文件上传
    (r'/api/file/upload', FileUploadHandler),
    (r'/api/file/update', FileUpdateHandler),
    (r'/api/file/list', FileListHandler),
    (r'/api/file/([\w\W]+)/pages', FileTotalHandler),
    (r'/api/file/predownload/([\w\W]+)', FileDownloadPreHandler),
    (r'/api/file/download/([\w\W]+)', FileDownloadHandler),
    (r'/api/file/delete', FileDeleteHandler),
    (r'/api/file/dir/create', FileDirCreateHandler),
    (r'/api/file/([\w\W]+)', FileInfoHandler),

]
