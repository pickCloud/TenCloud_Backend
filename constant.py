__author__ = 'Jon'

'''
程序的常量
'''

#################################################################################################
# 时间相关
#################################################################################################
FULL_DATE_FORMAT = '%Y-%m-%d %H:%i:%S'
FULL_DATE_FORMAT_ESCAPE = '%%Y-%%m-%%d %%H:%%i:%%S'
IMAGEHUB_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

#################################################################################################
# redis相关
#################################################################################################
DEPLOYING = 'deploying'
DEPLOYED  = 'deployed'
DEPLOYED_FLAG = '1'
AUTH_CODE = 'auth_code_{mobile}'
AUTH_CODE_ERROR_COUNT = 'auth_code_error_count_{mobile}'
AUTH_LOCK = 'auth_lock_{mobile}'
AUTH_LOCK_TIMEOUT = 7200 # 两个小时
AUTH_CODE_ERROR_COUNT_LIMIT = 10
SMS_FREQUENCE_LOCK = 'sms_frequence_lock_{mobile}'
SMS_FREQUENCE_LOCK_TIMEOUT = 60 # 一分钟
SMS_SENT_COUNT = 'sms_sent_count_{mobile}'
SMS_SENT_COUNT_LIMIT = 10
SMS_NEED_GEETEST_COUNT = 3
SMS_SENT_COUNT_LIMIT_TIMEOUT = 86400 # 一天， 也是验证码锁定次数超时
SESSION_KEY = 'session_{user_id}'
GIT_TOKEN = 'git_token'
CLUSTER_SEARCH_TIMEOUT = 60 # 集群搜索结果缓存超时
LOGOUT_CID = 'logout_cid'  # 记住退出时的状态，个人或是公司，方便下次登陆
COMPANY_PERMISSION = 'company_permissons'
USER_PERMISSION = 'cid_{cid}:uid_{uid}'
PERMISSIONS_FLAG = 1

#################################################################################################
# 错误代码及信息
#################################################################################################
ERR_TIP = {
    # 注册与登陆
    'no_registered':     {'sts': 10403, 'msg': '账号不存在。'},
    'no_registered_jump':     {'sts': 10404, 'msg': '你的账户还未注册，请先注册账户。'},
    'sms_over_three':    {'sts': 10405, 'msg': '该手机号码发送短信超过3次'},
    'sms_over_limit':      {'sts': 10407, 'msg': '每个手机号24小时内仅允许有10次获取短信验证码的机会，请24小时后再尝试'},
    'sms_too_frequency': {'sts': 10408, 'msg': '一分钟内一个手机只能发送一次'},
    'fail_in_geetest':   {'sts': 10409, 'msg': '人机验证失败'},
    'password_error':    {'sts': 10410, 'msg': '密码不正确，请确认后重新登录。'},
    'mobile_has_exist':    {'sts': 10411, 'msg': '该手机号已被注册。'},
    'auth_code_has_error': {'sts': 10412, 'msg': '登陆验证码错误{count}次'},
    'auth_code_many_errors': {'sts': 10413, 'msg': '登陆验证码已连续错{count}次，请二个小时后再次尝试'.format(count=AUTH_CODE_ERROR_COUNT_LIMIT)},
    'auth_code_timeout':   {'sts': 10414, 'msg': '短信验证码已过期，请重新获取'},

    # 公司
    'company_exists': {'sts': 10000, 'msg': '企业已存在，可以让管理员邀请加入。'},
    'is_employee':    {'sts': 10001, 'msg': '已是企业员工，无需重复添加企业。'},
    'company_name_repeat': {'sts': 10002, 'msg': '公司名字重复，请重新输入'},

    # server
    'server_name_repeat': {'sts': 10501, 'msg': '名称不能重复'}
}

#################################################################################################
# ssh相关
#################################################################################################
SSH_CONNECT_TIMEOUT = 30
SERVER_HOST = 'c.10.com'
SERVER_URL = 'https://' + SERVER_HOST
MONITOR_CMD = 'curl -sSL https://{host}/supermonitor/install.sh | sh '.format(host=SERVER_HOST)
UNINSTALL_CMD = 'curl -sSL https://{host}/supermonitor/uninstall.sh | sh '.format(host=SERVER_HOST)
CREATE_IMAGE_CMD = 'curl -sSL https://{host}/supermonitor/scripts/create-image.sh | sh -s '.format(host=SERVER_HOST)
IMAGE_INFO_CMD = 'docker images %s --format "{{.Tag}},{{.CreatedAt}}" | sed -n 1,3p'
REPOS_DOMAIN = 'hub.10.com'
DEPLOY_CMD = 'echo {password} | docker login {repository} -u {username} --password-stdin && docker pull {image_name} && docker run {portmap} -d --name {container_name} {image_name} '
LIST_CONTAINERS_CMD = 'docker ps -a --format "{{.ID}},{{.Names}},{{.Status}},{{.CreatedAt}}"'
CONTAINER_INFO_CMD = 'docker inspect --format "{{json .}}" %s'
START_CONTAINER_CMD = 'docker start {container_id}'
STOP_CONTAINER_CMD = 'docker stop {container_id}'
DEL_CONTAINER_CMD = STOP_CONTAINER_CMD + ' && docker rm {container_id}'
LOAD_IMAGE_FILE = 'docker load --input {filename}'
LOAD_IMAGE = """|tail -1|cut -d ' ' -f 3|awk '{b="docker tag "$0" hub.10.com/library/"$0; system(b); c="docker push hub.10.com/library/"$0; system(c)}'"""

CLOUD_DOWNLOAD_IMAGE = 'wget -b -c --tries=3 --directory-prefix={store_path} {image_url}'

#################################################################################################
# 阿里云相关
#################################################################################################
ALIYUN_NAME = '阿里云'
ALIYUN_DOMAIN = 'http://ecs.aliyuncs.com/?'
ALIYUN_REGION_NAME = {
    'cn-qingdao': '华北 1 （青岛）',
    'cn-beijing': '华北 2 （北京）',
    'cn-zhangjiakou': '华北 3 (张家口)',
    'cn-hangzhou': '华东 1 （杭州）',
    'cn-shanghai': '华东 2 （上海）',
    'cn-shenzhen': '华南 1 （深圳）',
    'cn-hongkong': '香港',
    'ap-southeast-1': '亚太东南 1 （新加坡）',
    'ap-southeast-2': '亚太东南 2 （悉尼）',
    'ap-northeast-1': '亚太东北 1 （日本）',
    'us-west-1': '美国西部 1 （硅谷）',
    'us-east-1': '美国东部 1 （弗吉尼亚)',
    'eu-central-1': '欧洲中部 1（法兰克福）',
    'me-east-1': '中东东部 1（迪拜）'
}
ALIYUN_REGION_LIST = ALIYUN_REGION_NAME.keys()

ALIYUN_STATUS = {
    'Pending': '准备中',
    'Stopped': '已停止',
    'Starting': '启动中',
    'Running': '运行中',
    'Stopping': '停止中',
    'Deleted': '已释放'
}

#################################################################################################
# 腾讯云相关
#################################################################################################
QCLOUD_NAME = '腾讯云'
QCLOUD_DOMAIN = 'https://cvm.api.qcloud.com/v2/index.php?'
QCLOUD_HOST = QCLOUD_DOMAIN[8:-1]
QCLOUD_REGION_NAME = {
    'ap-guangzhou': '华南地区（广州）',
    'ap-shenzhen-fsi': '华南地区（深圳金融）',
    'ap-shanghai': '华东地区（上海）',
    'ap-shanghai-fsi': '华东地区（上海金融）',
    'ap-beijing': '华北地区（北京）',
    'ap-hongkong': '东南亚地区（香港）',
    'ap-singapore': '东南亚地区（新加坡）',
    'na-toronto': '北美地区（多伦多）',
    'na-siliconvalley': '美国西部（硅谷）'
}
QCLOUD_REGION_LIST = QCLOUD_REGION_NAME.keys()

QCLOUD_STATUS = {
    1: '故障',
    2: '运行中',
    3: '创建中',
    4: '已关机',
    5: '已退还',
    6: '退还中',
    7: '重启中',
    8: '开机中',
    9: '关机中',
    10: '密码重置中',
    11: '格式化中',
    12: '镜像制作中',
    13: '带宽设置中',
    14: '重装系统中',
    15: '域名绑定中',
    16: '域名解绑中',
    17: '负载均衡绑定中',
    18: '负载均衡解绑中',
    19: '升级中',
    20: '密钥下发中',
}

QCLOUD_PAYMODE = {
    0: '按月结算的后付费',
    1: '包年包月',
    2: '按流量',
    3: '按带宽'
}

#################################################################################################
# 亚马逊云相关
#################################################################################################
ZCLOUD_NAME = '亚马逊云'
ZCLOUD_DOMAIN = 'https://ec2.amazonaws.com?'
ZCLOUD_HOST = ZCLOUD_DOMAIN[8:-1]
ZCLOUD_REGION_NAME = {
    'us-east-1': '美国东部 (弗吉尼亚北部) ',
    'us-east-2': '美国东部（俄亥俄）',
    'us-west-1': '美国西部（加利福尼亚北部）',
    'us-west-2': '美国西部（俄勒冈）',
    'ca-central-1': '加拿大（中部）',
    'eu-west-1': '欧洲 (爱尔兰)',
    'eu-central-1': '欧洲 (法兰克福) ',
    'eu-west-2': '欧洲 (伦敦) ',
    'ap-northeast-1': '亚太地区（东京）',
    'ap-northeast-2': '亚太地区域（首尔）',
    'ap-southeast-1': '亚太地区（新加坡）',
    'ap-southeast-2': '亚太地区（悉尼）',
    'ap-south-1': '亚太地区域（孟买）',
    'sa-east-1': '南美洲（圣保罗）'
}
ZCLOUD_REGION_LIST = ZCLOUD_REGION_NAME.keys()

ZCLOUD_TYPE = {
    # cpu, memory
    't2.nano': [1, 0.5],
    't2.micro': [1, 1],
    't2.small': [1, 2],
    't2.medium': [2, 4],
    't2.large': [2, 8],
    't2.xlarge': [4, 16],
    't2.2xlarge': [8, 32],
    'm4.large': [2, 8],
    'm4.xlarge': [4, 16],
    'm4.2xlarge': [8, 32],
    'm4.4xlarge': [16, 64],
    'm4.10xlarge': [40, 160],
    'm4.16xlarge': [64, 256],
    'm3.medium': [1, 3.75],
    'm3.large': [2, 7.5],
    'm3.xlarge': [4, 15],
    'm3.2xlarge': [8, 30],
    'c4.large': [2, 3.75],
    'c4.xlarge': [4, 7.5],
    'c4.2xlarge': [8, 15],
    'c4.4xlarge': [16, 30],
    'c4.8xlarge': [36, 60],
    'c3.large': [2, 3.75],
    'c3.xlarge': [4, 7.5],
    'c3.2xlarge': [8, 15],
    'c3.4xlarge': [16, 30],
    'c3.8xlarge': [32, 60],
    'x1.32xlarge': [128, 1952],
    'x1.16xlarge': [64, 976],
    'r4.large': [2, 15.25],
    'r4.xlarge': [4, 30.5],
    'r4.2xlarge': [8, 61],
    'r4.4xlarge': [16, 122],
    'r4.8xlarge': [32, 244],
    'r4.16xlarge': [64, 488],
    'r3.large': [2, 15.25],
    'r3.xlarge': [4, 30.5],
    'r3.2xlarge': [8, 61],
    'r3.4xlarge': [16, 122],
    'r3.8xlarge': [32, 244],
    'i3.large': [2, 15.25],
    'i3.xlarge': [4, 30.5],
    'i3.2xlarge': [8, 61],
    'i3.4xlarge': [16, 122],
    'i3.8xlarge': [32, 244],
    'i3.16xlarge': [64, 488],
    'd2.xlarge': [4, 30.5],
    'd2.2xlarge': [8, 61],
    'd2.4xlarge': [16, 122],
    'd2.8xlarge': [32, 244]
}

ZCLOUD_STATUS = {
    'pending': '准备中',
    'stopped': '已停止',
    'running': '运行中',
    'stopping': '停止中',
    'terminated': '已释放',
    'shutting-down': '释放中',
    'rebooting': '重启中'
}
#################################################################################################
# http相关
#################################################################################################
HTTP_TIMEOUT = 20
USER_AGENTS = [
    'Mozilla/5.0 (Linux; U; Android 2.3.6; en-us; Nexus S Build/GRK39F) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
    'Avant Browser/1.2.789rel1 (http://www.avantbrowser.com)',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.5 (KHTML, like Gecko) Chrome/4.0.249.0 Safari/532.5',
    'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/532.9 (KHTML, like Gecko) Chrome/5.0.310.0 Safari/532.9',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.601.0 Safari/534.14',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14',
    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.27 (KHTML, like Gecko) Chrome/12.0.712.0 Safari/534.27',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.24 Safari/535.1',
    'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.120 Safari/535.2',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.36 Safari/535.7',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0 x64; en-US; rv:1.9pre) Gecko/2008072421 Minefield/3.0.2pre',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.10) Gecko/2009042316 Firefox/3.0.10',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.0.11) Gecko/2009060215 Firefox/3.0.11 (.NET CLR 3.5.30729)',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 GTB5',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; tr; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 ( .NET CLR 3.5.30729; .NET4.0E)',
    'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
    'Mozilla/5.0 (Windows NT 5.1; rv:5.0) Gecko/20100101 Firefox/5.0',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0a2) Gecko/20110622 Firefox/6.0a2',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:7.0.1) Gecko/20100101 Firefox/7.0.1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b4pre) Gecko/20100815 Minefield/4.0b4pre',
    'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.0 )',
    'Mozilla/4.0 (compatible; MSIE 5.5; Windows 98; Win 9x 4.90)',
    'Mozilla/5.0 (Windows; U; Windows XP) Gecko MultiZilla/1.6.1.0a',
    'Mozilla/2.02E (Win95; U)',
    'Mozilla/3.01Gold (Win95; I)',
    'Mozilla/4.8 [en] (Windows NT 5.1; U)',
    'Mozilla/5.0 (Windows; U; Win98; en-US; rv:1.4) Gecko Netscape/7.1 (ax)',
    'HTC_Dream Mozilla/5.0 (Linux; U; Android 1.5; en-ca; Build/CUPCAKE) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1',
    'Mozilla/5.0 (hp-tablet; Linux; hpwOS/3.0.2; U; de-DE) AppleWebKit/534.6 (KHTML, like Gecko) wOSBrowser/234.40.1 Safari/534.6 TouchPad/1.0',
    'Mozilla/5.0 (Linux; U; Android 1.5; en-us; sdk Build/CUPCAKE) AppleWebkit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1',
    'Mozilla/5.0 (Linux; U; Android 2.1; en-us; Nexus One Build/ERD62) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17',
    'Mozilla/5.0 (Linux; U; Android 2.2; en-us; Nexus One Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
    'Mozilla/5.0 (Linux; U; Android 1.5; en-us; htc_bahamas Build/CRB17) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1',
    'Mozilla/5.0 (Linux; U; Android 2.1-update1; de-de; HTC Desire 1.19.161.5 Build/ERE27) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17',
    'Mozilla/5.0 (Linux; U; Android 2.2; en-us; Sprint APA9292KT Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
    'Mozilla/5.0 (Linux; U; Android 1.5; de-ch; HTC Hero Build/CUPCAKE) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1',
    'Mozilla/5.0 (Linux; U; Android 2.2; en-us; ADR6300 Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
    'Mozilla/5.0 (Linux; U; Android 2.1; en-us; HTC Legend Build/cupcake) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17',
    'Mozilla/5.0 (Linux; U; Android 1.5; de-de; HTC Magic Build/PLAT-RC33) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1 FirePHP/0.3',
    'Mozilla/5.0 (Linux; U; Android 1.6; en-us; HTC_TATTOO_A3288 Build/DRC79) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1',
    'Mozilla/5.0 (Linux; U; Android 1.0; en-us; dream) AppleWebKit/525.10  (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2',
    'Mozilla/5.0 (Linux; U; Android 1.5; en-us; T-Mobile G1 Build/CRB43) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari 525.20.1',
    'Mozilla/5.0 (Linux; U; Android 1.5; en-gb; T-Mobile_G2_Touch Build/CUPCAKE) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1',
    'Mozilla/5.0 (Linux; U; Android 2.0; en-us; Droid Build/ESD20) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17',
    'Mozilla/5.0 (Linux; U; Android 2.2; en-us; Droid Build/FRG22D) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
    'Mozilla/5.0 (Linux; U; Android 2.0; en-us; Milestone Build/ SHOLS_U2_01.03.1) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17',
    'Mozilla/5.0 (Linux; U; Android 2.0.1; de-de; Milestone Build/SHOLS_U2_01.14.0) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17',
    'Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/525.10  (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2',
    'Mozilla/5.0 (Linux; U; Android 0.5; en-us) AppleWebKit/522  (KHTML, like Gecko) Safari/419.3',
    'Mozilla/5.0 (Linux; U; Android 1.1; en-gb; dream) AppleWebKit/525.10  (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2',
    'Mozilla/5.0 (Linux; U; Android 2.0; en-us; Droid Build/ESD20) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17',
    'Mozilla/5.0 (Linux; U; Android 2.1; en-us; Nexus One Build/ERD62) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17',
    'Mozilla/5.0 (Linux; U; Android 2.2; en-us; Sprint APA9292KT Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
    'Mozilla/5.0 (Linux; U; Android 2.2; en-us; ADR6300 Build/FRF91) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
    'Mozilla/5.0 (Linux; U; Android 2.2; en-ca; GT-P1000M Build/FROYO) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1',
    'Mozilla/5.0 (Linux; U; Android 3.0.1; fr-fr; A500 Build/HRI66) AppleWebKit/534.13 (KHTML, like Gecko) Version/4.0 Safari/534.13',
    'Mozilla/5.0 (Linux; U; Android 3.0; en-us; Xoom Build/HRI39) AppleWebKit/525.10  (KHTML, like Gecko) Version/3.0.4 Mobile Safari/523.12.2',
    'Mozilla/5.0 (Linux; U; Android 1.6; es-es; SonyEricssonX10i Build/R1FA016) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1',
    'Mozilla/5.0 (Linux; U; Android 1.6; en-us; SonyEricssonX10i Build/R1AA056) AppleWebKit/528.5  (KHTML, like Gecko) Version/3.1.2 Mobile Safari/525.20.1',
]

#################################################################################################
# git相关
#################################################################################################
GIT_REPOS_URL = 'https://api.github.com/user/repos'
GIT_BRANCH_URL = 'https://api.github.com/repos/{repos_name}/branches'
GIT_FETCH_TOKEN_URL = 'https://github.com/login/oauth/access_token'
GIT_FETCH_CODE_URL = 'https://github.com/login/oauth/authorize'
GIT_CALLBACK = 'https://' + SERVER_HOST + '/api/github/oauth/callback'

#################################################################################################
# SMS相关
#################################################################################################
SMS_EXISTS_TIME = 86400 # 验证码存在的时间
SMS_TIMEOUT = 600 # 验证码有效期10分钟

#################################################################################################
# Session相关
#################################################################################################
COOKIE_EXPIRES_DAYS = 7  # 一周
TOKEN_EXPIRES_DAYS = 7   # 一周
SESSION_TIMEOUT = 604800 # 一周

#################################################################################################
# 其他
#################################################################################################
POOL_COUNT = 10
AES_KEY = '01234^!@#$%56789'
QINIU_POLICY = {
    "returnBody":
        """
        {"size": $(fsize), "type": $(mimeType), "key": $(key)}
        """,
    "persistentOps": "",
    "persistentPipeline": ""
}
QINIU_THUMB = 'imageView2/1/w/50/h/50/format/webp/q/75|imageslim'
NEG = '~'


#################################################################################################
# Tornado
#################################################################################################
TORNADO_MAX_BODY_SIZE = 1*1024*1024*1024


#################################################################################################
# 项目状态
# 0 初创建, 1 构建中, 2 构建成功, 3 部署中， 4 部署成功, -2 构建失败, -4 部署失败',
#################################################################################################
PROJECT_STATUS = dict()
PROJECT_STATUS['init'] = 0
PROJECT_STATUS['building'] = 1
PROJECT_STATUS['build-success'] = 2
PROJECT_STATUS['deploying'] = 3
PROJECT_STATUS['deploy-success'] = 4
PROJECT_STATUS['build-failure'] = -2
PROJECT_STATUS['deploy-failure'] = -4

#################################################################################################
# 文件上传
#################################################################################################
DISK_DOWNLOAD_URL = 'https://' + SERVER_HOST + '/api/file/download/'

# 分页时，单页面最大100条
MAX_PAGE_NUMBER = 100

#################################################################################################
# 操作状态码
#################################################################################################
OPERATE_STATUS = dict()
OPERATE_STATUS['success'] = 0
OPERATE_STATUS['fail'] = 1

#################################################################################################
# 操作对象类型
#################################################################################################
OPERATION_OBJECT_STYPE = dict()
OPERATION_OBJECT_STYPE['server'] = 0
OPERATION_OBJECT_STYPE['container'] = 1
OPERATION_OBJECT_STYPE['project'] = 2

#################################################################################################
# 主机操作行为码
#################################################################################################
SERVER_OPERATE_STATUS = dict()
SERVER_OPERATE_STATUS['start'] = 0
SERVER_OPERATE_STATUS['stop'] = 1
SERVER_OPERATE_STATUS['reboot'] = 2
SERVER_OPERATE_STATUS['change'] = 3

#################################################################################################
# 容器操作行为码
#################################################################################################
CONTAINER_OPERATE_STATUS = dict()
CONTAINER_OPERATE_STATUS['start'] = 0
CONTAINER_OPERATE_STATUS['stop'] = 1
CONTAINER_OPERATE_STATUS['reboot'] = 2
CONTAINER_OPERATE_STATUS['delete'] = 3

#################################################################################################
# 项目操作行为码
#################################################################################################
PROJECT_OPERATE_STATUS = dict()
PROJECT_OPERATE_STATUS['create'] = 0
PROJECT_OPERATE_STATUS['build'] = 1
PROJECT_OPERATE_STATUS['deploy'] = 2
PROJECT_OPERATE_STATUS['change'] = 3
PROJECT_OPERATE_STATUS['delete'] = 5
PROJECT_OPERATE_STATUS['delete_log'] = 5

#################################################################################################
# Websocket相关
#################################################################################################
SUCCESS = 'success'
FAILURE = 'failure'

#################################################################################################
# docker run 宿主机到容器的端口映射
#################################################################################################
YE_PORTMAP = '-p 80:80 -p 8080:8080 -p 8888:8888 -p 9999:9999'

#################################################################################################
# 公司相关
#################################################################################################
DEFAULT_ENTRY_SETTING = 'mobile,name'
INVITE_URL = SERVER_URL + '/#/invite?code='
APPLICATION_STATUS = {
    'reject': -1,
    'process': 0,
    'accept': 1,
    'founder': 2
}
MSG = {
    'application': {
        'admin': '【{name}】【{mobile}】申请加入【{company_name}】，请及时审核 ',
        'accept': '【{admin_name}】审核通过了你加入【{company_name}】的申请，你可以进入企业了',
        'reject': '【{admin_name}】拒绝了你加入【{company_name}】的申请，你可以核对信息后重新提交申请',
    },
    'change': '你的企业【{company_name}】被管理员 【{admin_name}】修改了资料',
    'leave': {
        'dismission': '【{name}】【{mobile}】离开了【{company_name}】',
        'demission': '【{name}】【{mobile}】离开了【{company_name}】',
    }
}
MSG_MODE = {
    'application': 1,
    'change': 2,
    'leave': 3
}
MSG_STATUS = {
    'unread': 0,
    'read': 1
}
MSG_SUB_MODE = {
    'verify': 0,
    'reject': 1,
    'accept': 2,
    'change': 3
}
MSG_PAGE_NUM = 20

#################################################################################################
# 权限模版 0云服务器, 1项目, 2文件服务, 3企业资料, 4员工管理, 5权限模版管理, 6平台管理
#################################################################################################
PERMISSIONS = ["云服务器", "项目", "文件服务", "企业资料", "员工管理", "权限模版管理", "平台管理"]
PT_FORMAT = 1