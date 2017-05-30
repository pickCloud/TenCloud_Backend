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
CMD_MONITOR = 'curl -sSL http://{host}/supermonitor/install.sh | sh'.format(host=SERVER_HOST)