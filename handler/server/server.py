__author__ = 'Jon'

import traceback
import json


from tornado.websocket import WebSocketHandler
from tornado.gen import coroutine, Task
from tornado.ioloop import PeriodicCallback, IOLoop
from handler.base import BaseHandler
from constant import DEPLOYING, DEPLOYED, DEPLOYED_FLAG, ALIYUN_REGION_NAME
from utils.general import validate_ip
from utils.security import Aes
from constant import MONITOR_CMD


class ServerNewHandler(WebSocketHandler, BaseHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self.write_message('open')

    def on_message(self, message):
        self.params = json.loads(message)

        # 参数认证
        try:
            args = ['cluster_id', 'name', 'public_ip', 'username', 'passwd']

            self.guarantee(*args)

            for i in args[1:]:
                self.params[i] = self.params[i].strip()

            validate_ip(self.params['public_ip'])
        except Exception as e:
            self.write_message(str(e))
            self.close()
            return

        IOLoop.current().spawn_callback(callback=self.handle_msg)  # on_message不能异步, 要实现异步需spawn_callback

    @coroutine
    def handle_msg(self):
        is_deploying = yield Task(self.redis.hget, DEPLOYING, self.params['public_ip'])

        is_deployed = yield Task(self.redis.hget, DEPLOYED, self.params['public_ip'])


        if is_deploying:
            self.write_message('%s 正在部署' % self.params['public_ip'])
            return

        if is_deployed:
            self.write_message('%s 之前已部署' % self.params['public_ip'])
            return

        # 保存到redis之前加密
        passwd = self.params['passwd']
        self.params['passwd'] = Aes.encrypt(passwd)

        yield Task(self.redis.hset, DEPLOYING, self.params['public_ip'], json.dumps(self.params))

        self.period = PeriodicCallback(self.check, 3000)  # 设置定时函数, 3秒
        self.period.start()

        self.params.update({'passwd': passwd})
        err_msg = yield self.server_service.remote_ssh(self.params, cmd=MONITOR_CMD)

        # 部署失败
        if err_msg:
            self.write_message(err_msg)
            self.period.stop()
            self.close()

            yield Task(self.redis.hdel, DEPLOYING, self.params['public_ip'])

    @coroutine
    def check(self):
        ''' 检查主机是否上报信息 '''
        result = yield Task(self.redis.hget, DEPLOYED, self.params['public_ip'])

        if result:
            self.write_message('success')
            self.period.stop()
            self.close()

    def on_close(self):
        if hasattr(self, 'period'):
            self.period.stop()


class ServerReport(BaseHandler):
    @coroutine
    def post(self):
        try:
            deploying_msg = yield Task(self.redis.hget, DEPLOYING, self.params['public_ip'])

            is_deployed = yield Task(self.redis.hget, DEPLOYED, self.params['public_ip'])

            if not deploying_msg and not is_deployed:
                raise ValueError('%s not in deploying/deployed' % self.params['public_ip'])

            if deploying_msg:
                data = json.loads(deploying_msg)
                self.params.update({
                    'name': data['name'],
                    'cluster_id': data['cluster_id']
                })

                yield self.server_service.add_server(self.params)
                yield self.server_service.save_server_account({'username': data['username'],
                                                               'passwd': data['passwd'],
                                                               'public_ip': data['public_ip']})
                yield Task(self.redis.hdel, DEPLOYING, self.params['public_ip'])
                yield Task(self.redis.hset, DEPLOYED, self.params['public_ip'], DEPLOYED_FLAG)

            yield self.server_service.save_report(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerMigratinHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 主机迁移
            参数: id -> []
        '''
        try:
            yield self.server_service.migrate_server(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerDelHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 主机删除
            参数: id -> []
        '''
        try:
            yield self.server_service.delete_server(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerDetailHandler(BaseHandler):
    @coroutine
    def get(self, id):
        ''' 主机详情
        '''
        try:
            data = yield self.server_service.get_detail(id)

            result = dict()

            result['basic_info'] = {
                'id': data['id'],
                'name': data['name'],
                'cluster_id': data['cluster_id'],
                'cluster_name': data['cluster_name'],
                'address': ALIYUN_REGION_NAME.get(data['region_id']),
                'public_ip': data['public_ip'],
                'machine_status': data['machine_status'],
                'business_status': data['business_status']
            }

            result['system_info'] = {
                'config': {
                    'cpu': data['cpu'],
                    'memory': data['memory'],
                    'os_name': data['os_name'],
                    'os_type': data['os_type']
                }
            }

            result['business_info'] = {
                'provider': data['provider'],
                'contract': {
                    'create_time': data['create_time'],
                    'expired_time': data['expired_time'],
                    'charge_type': data['charge_type']
                }
            }

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerPerformanceHandler(BaseHandler):
    @coroutine
    def post(self):
        try:
            data = yield self.server_service.get_performance(self.params)
            self.success(data)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerUpdateHandler(BaseHandler):
    @coroutine
    def post(self):
        try:
            yield self.server_service.update_server(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerStopHandler(BaseHandler):
    @coroutine
    def get(self, id):
        ''' 停止主机
        '''
        try:
            yield self.server_service.stop_server(id)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerStartHandler(BaseHandler):
    @coroutine
    def get(self, id):
        ''' 开启主机
        '''
        try:
            yield self.server_service.start_server(id)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())

class ServerRebootHandler(BaseHandler):
    @coroutine
    def get(self, id):
        ''' 重启主机
        '''
        try:
            yield self.server_service.reboot_server(id)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerDockerContainersHandler(BaseHandler):
    @coroutine
    def get(self, id):
        ''' 获取主机里面的docker容器列表
        '''
        try:
            data, err = yield self.server_service.get_docker_containers(id)

            if err:
                self.error(err)
                return

            self.success(data)
        except:
            self.error()
            self.log.error(traceback.format_exc())