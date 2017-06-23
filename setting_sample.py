__author__ = 'Jon'

'''
项目配置文件, 对外, 比如项目的启动端口/数据库配置/api域名配置
'''

settings = dict()

# 端口
settings['port'] = 8010

# 是否开启debug
settings['debug'] = True

# MYSQL配置
settings['mysql_host'] = 'localhost'
settings['mysql_port'] = 3306
settings['mysql_database'] = 'ten_dashboard'
settings['mysql_user'] = 'root'
settings['mysql_password'] = '123456'
settings['mysql_charset'] = 'utf8mb4'

# REDIS配置
settings['redis_host'] = 'localhost'
settings['redis_port'] = 6379

# 阿里access_key
settings['aliyun_id'] = ''
settings['aliyun_secret'] = ''

# Git token
settings['git_token'] = ''
