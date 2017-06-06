__author__ = 'Jon'

'''
程序的常量
'''

# 时间格式
CLUSTER_DATE_FORMAT = '%Y年%m月%d日'
CLUSTER_DATE_FORMAT_ESCAPE = '%%Y年%%m月%%d日'
IMAGEHUB_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 添加主机的redis key
DEPLOYING = 'deploying'
DEPLOYED  = 'deployed'
DEPLOYED_FLAG = '1'

# 线程池数量
POOL_COUNT = 10

# 密码加密的key
AES_KEY = '01234^!@#$%56789'

# 远程连接主机
SSH_CONNECT_TIMEOUT = 30
SERVER_HOST = '47.94.18.22'
MONITOR_FILE = '/etc/init.d/install.sh'
MONITOR_CMD = 'curl -sSL http://{host}/supermonitor/install.sh -o {file} && chmod a+x {file} && source {file}'.format(host=SERVER_HOST, file=MONITOR_FILE)

# 阿里云的region列表
ALIYUN_DOMAIN = 'http://ecs.aliyuncs.com/?'

# 阿里云地区名称转换
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

# HTTP超时时间
HTTP_TIMEOUT = 20

# 主机开机/关机/重启对应的状态
INSTANCE_STATUS = {
    'StartInstance': 'Running',
    'StopInstance': 'Stopped',
    'RebootInstance': 'Running'
}
