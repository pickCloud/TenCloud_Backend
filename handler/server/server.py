__author__ = 'Jon'

import traceback
import json


from tornado.websocket import WebSocketHandler
from tornado.gen import coroutine, Task
from tornado.ioloop import PeriodicCallback, IOLoop
from handler.base import BaseHandler
from constant import DEPLOYING, DEPLOYED, DEPLOYED_FLAG
from utils.general import validate_ip
from utils.security import Aes


class ServerNewHandler(WebSocketHandler, BaseHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        self.write_message('open')

    def on_message(self, message):
        self.params = json.loads(message)

        # 参数认证
        try:
            args = ['cluster_id', 'name', 'ip', 'username', 'passwd']

            self.guarantee(*args)

            for i in args[1:]:
                self.params[i] = self.params[i].strip()

            validate_ip(self.params['ip'])
        except Exception as e:
            self.write_message(str(e))
            self.close()
            return

        IOLoop.current().spawn_callback(callback=self.handle_msg) # on_message不能异步, 要实现异步需spawn_callback

    @coroutine
    def handle_msg(self):
        is_deploying = yield Task(self.redis.hget, DEPLOYING, self.params['ip'])
        is_deployed  = yield Task(self.redis.hget, DEPLOYED, self.params['ip'])

        if is_deploying:
            self.write_message('%s 正在部署' % self.params['ip'])
            return

        if is_deployed:
            self.write_message('%s 之前已部署' % self.params['ip'])
            return

        # 保存到redis之前加密
        passwd = self.params['passwd']
        self.params['passwd'] = Aes.encrypt(passwd)

        yield Task(self.redis.hset, DEPLOYING, self.params['ip'], json.dumps(self.params))

        self.period = PeriodicCallback(self.check, 3000)  # 设置定时函数, 3秒
        self.period.start()

        self.params.update({'passwd': passwd})
        yield self.server_service.remote_deploy(self.params)

    @coroutine
    def check(self):
        ''' 检查主机是否上报信息 '''
        result = yield Task(self.redis.hget, DEPLOYED, self.params['ip'])

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
            deploying_msg = yield Task(self.redis.hget, DEPLOYING, self.params['ip'])
            is_deployed   = yield Task(self.redis.hget, DEPLOYED, self.params['ip'])

            if not deploying_msg and not is_deployed:
                raise ValueError('%s not in deploying/deployed' % self.params['ip'])

            if deploying_msg:
                data = json.loads(deploying_msg)

                self.params.update({
                    'name': data['name'],
                    'cluster_id': data['cluster_id']
                })

                yield self.server_service.save_server_account({'username': data['username'],
                                                               'passwd': data['passwd'],
                                                               'ip': data['ip']})
                yield Task(self.redis.hdel, DEPLOYING, self.params['ip'])
                yield Task(self.redis.hset, DEPLOYED, self.params['ip'], DEPLOYED_FLAG)

            yield self.server_service.save_report(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerMigratinHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 主机迁移
        '''
        try:
            yield self.server_service.migrate_server(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ServerDeletionHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 主机删除
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
            data = yield self.server_service.select(conds=['id=%s'], params=[id], one=True)

            result = dict()

            result['basic_info'] = {
                'id': data['id'],
                'name': data['name'],
                'address': data['address'],
                'ip': data['ip'],
                'machine_status': data['machine_status'],
                'business_status': data['business_status']
            }

            result['system_info'] = {
                'config': {
                    'cpu': json.loads(data['cpu']),
                    'memory': json.loads(data['memory']),
                    'disk': json.loads(data['disk'])
                }
            }

            result['business_info'] = {
                'provider': data['provider'],
                'contract': {
                    'period': data['period'],
                    'pay_type': data['pay_type']
                }
            }

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())
