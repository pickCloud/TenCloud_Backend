__author__ = 'Jon'

import json
import re

from tornado.gen import coroutine
from tornado.ioloop import PeriodicCallback, IOLoop
from handler.base import BaseHandler, WebSocketBaseHandler
from constant import DEPLOYING, DEPLOYED, DEPLOYED_FLAG, ERR_TIP
from utils.general import validate_ip
from utils.security import Aes
from utils.decorator import is_login, require
from utils.context import catch
from constant import MONITOR_CMD, OPERATE_STATUS, OPERATION_OBJECT_STYPE, SERVER_OPERATE_STATUS, \
      CONTAINER_OPERATE_STATUS, RIGHT, SERVICE, FORM_COMPANY, SERVERS_REPORT_INFO, THRESHOLD, FORM_PERSON


class ServerNewHandler(WebSocketBaseHandler):
    def on_message(self, message):
        self.params.update(json.loads(message))

        # 参数认证
        try:
            args = ['cluster_id', 'name', 'public_ip', 'username', 'passwd']

            self.guarantee(*args)

            for i in args[1:]:
                self.params[i] = self.params[i].strip()

            validate_ip(self.params['public_ip'])

            self.params.update(self.get_lord())
            self.params.update({'owner': self.current_user['id']})
        except Exception as e:
            self.write_message(str(e))
            self.close()
            return

        IOLoop.current().spawn_callback(callback=self.handle_msg)  # on_message不能异步, 要实现异步需spawn_callback

    @coroutine
    def handle_msg(self):
        is_deploying = self.redis.hget(DEPLOYING, self.params['public_ip'])
        is_deployed  = self.redis.hget(DEPLOYED, self.params['public_ip'])

        # 通知主机添加失败，后续需要将主机添加失败原因进行抽象分类告知用户
        message = {
            'owner': self.params.get('owner'),
            'ip': self.params['public_ip'],
            'tip': '{}'.format(self.params.get('lord') if self.params.get('form') == FORM_COMPANY else 0)
        }

        if is_deploying:
            reason = '%s 正在部署' % self.params['public_ip']
            self.write_message(reason)
            self.write_message('failure')
            message['reason'] = reason
            yield self.message_service.notify_server_add_failed(message)
            return

        if is_deployed:
            reason = '%s 之前已部署' % self.params['public_ip']
            self.write_message(reason)
            self.write_message('failure')
            message['reason'] = reason
            yield self.message_service.notify_server_add_failed(message)
            return

        # 保存到redis之前加密
        passwd = self.params['passwd']
        self.params['passwd'] = Aes.encrypt(passwd)

        self.redis.hset(DEPLOYING, self.params['public_ip'], json.dumps(self.params))

        self.period = PeriodicCallback(self.check, 3000)  # 设置定时函数, 3秒
        self.period.start()

        self.params.update({'passwd': passwd, 'cmd': MONITOR_CMD, 'rt': True, 'out_func': self.write_message})
        _, err = yield self.server_service.remote_ssh(self.params)

        err = [e for e in err if not re.search(r'symlink|resolve host', e)] # 忽略某些错误

        # 部署失败
        if err:
            if err[0] == 'Authentication failed.':
                reason = '认证失败'
                self.write_message(reason)
                message['reason'] = reason
                yield self.message_service.notify_server_add_failed(message)
            self.write_message('failure')
            self.period.stop()
            self.close()

            self.redis.hdel(DEPLOYING, self.params['public_ip'])


    def check(self):
        ''' 检查主机是否上报信息 '''
        result = self.redis.hget(DEPLOYED, self.params['public_ip'])

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
        """
        @api {post} /remote/server/report 监控上报
        @apiName ServerReport
        @apiGroup Server

        @apiParam {String} public_ip 公共ip
        @apiParam {Number} time 时间戳
        @apiParam {map[Number]Object} docker 容器
        @apiParam {Object} cpu CPU
        @apiParam {Object} memory Memory
        @apiParam {Object} disk Disk
        @apiParam {Object} net Net
        @apiParam {Object} system_load 负载

        @apiUse Success
        """
        with catch(self):
            deploying_msg = self.redis.hget(DEPLOYING, self.params['public_ip'])
            is_deployed = self.redis.hget(DEPLOYED, self.params['public_ip'])

            if not deploying_msg and not is_deployed:
                raise ValueError('%s not in deploying/deployed' % self.params['public_ip'])

            if deploying_msg:
                data = json.loads(deploying_msg)
                self.params.update({
                    'name': data['name'],
                    'cluster_id': data['cluster_id'],
                    'lord': data['lord'],
                    'form': data['form']
                })

                yield self.server_service.add_server(self.params)
                yield self.server_service.save_server_account({'username': data['username'],
                                                               'passwd': data['passwd'],
                                                               'public_ip': data['public_ip']})
                self.redis.hdel(DEPLOYING, self.params['public_ip'])
                self.redis.hset(DEPLOYED, self.params['public_ip'], DEPLOYED_FLAG)

                # 通知服务器创建成功消息
                server_id = yield self.server_service.fetch_server_id(self.params['public_ip'])
                instance_info = yield self.server_service.fetch_instance_info(server_id)
                message = {
                    'owner': data.get('owner'),
                    'ip': self.params.get('public_ip'),
                    'provider': instance_info['provider'],
                    'tip': '{}'.format(data['lord'] if data['form'] == FORM_COMPANY else 0)
                }

                # 添加非个人机器时给添加者授予新增主机的数据权限，并且也通知到管理员
                if self.params['form'] == FORM_COMPANY:
                    arg = {
                        'cid': self.params['lord'],
                        'uid': data.get('owner'),
                        'sid': server_id
                    }
                    yield self.user_access_server_service.add(arg)

                    admin = yield self.company_employee_service.select(conds={'cid': self.params['lord'], 'is_admin': 1}, one=True)
                    if data.get('owner') != admin['uid']:
                        message['admin'] = admin['uid']

                yield self.message_service.notify_server_added(message)

            yield self.server_service.save_report(self.params)

            self.success()


class ServerDelHandler(BaseHandler):
    @require(RIGHT['delete_server'], service=SERVICE['s'])
    @coroutine
    def post(self):
        """
        @api {post} /api/server/del 主机删除
        @apiName ServerDelHandler
        @apiGroup Server

        @apiUse cidHeader

        @apiParam {Number[]} id 主机ID

        @apiUse Success
        """
        with catch(self):
            yield self.server_service.delete_server(self.params)
            self.success()


class ServerDetailHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def get(self, id):
        """
        @api {get} /api/server/(\d+) 主机详情
        @apiName ServerDetailHandler
        @apiGroup Server

        @apiParam {Number} id 主机ID

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
            "status": 0,
            "msg": "success",
            "data": {
                "basic_info": {
                    "id": int,
                    "name": str,
                    "cluster_id": int,
                    "cluster_name": str,
                    "address": str,
                    "public_ip": str,
                    "machine_status": str,
                    "business_status": str,
                    "region_id": str,
                    "instance_id": str
                },
                "system_info": {
                    "config": {
                        "cpu": int,
                        "memory": str,
                        "os_name": str,
                        "os_type": str,
                        "security_group_ids": [],
                        "instance_network_type": str,
                        "internetMaxBandwidthIn": str,
                        "internetMaxBandwidthOut": str,
                        "image_info":[
                            {
                                "image_id": str,
                                "image_name": str,
                                "image_version": str
                            }
                            ...
                        ],
                        "disk_info":[
                            {
                                "system_disk_id": str,
                                "system_disk_type": str,
                                "system_disk_size": str,
                                "image_id": str,
                                "image_version": str,
                                "image_name": str
                            }
                            ...
                        ]
                    }
                },
                "business_info": {
                    "provider": str,
                    "contract": {
                        "create_time": str,
                        "expired_time": str,
                        "charge_type": str
                    }
                },
            }
            }
        """
        with catch(self):
            data = yield self.server_service.get_detail(int(id))
            result = dict()

            result['basic_info'] = {
                'id': data['id'],
                'name': data['name'],
                'cluster_id': data['cluster_id'],
                'cluster_name': data['cluster_name'],
                'address': data['region_name'],
                'public_ip': data['public_ip'],
                'machine_status': data['machine_status'],
                'business_status': data['business_status'],
                'region_id': data['region_id'],
                'instance_id': data['instance_id'],
                'created_time': data['server_created_time']
            }

            disk_info = list()
            for i in json.loads(data.get('disk_info','')):
                one = dict()
                one['system_disk_id'] = i['DiskId']
                one['system_disk_type'] = i['DiskCategory']
                one['system_disk_size'] = str(i['DiskSize'])+"G"
                disk_info.append(one)

            image_info = list()
            for i in json.loads(data.get('image_info', '')):
                one = dict()
                one['image_id'] = i['ImageId']
                one['image_name'] = i['ImageName']
                one['image_version'] = i['ImageVersion']
                image_info.append(one)

            result['system_info'] = {
                'config': {
                    'cpu': data['cpu'],
                    'memory': data['memory'],
                    'os_name': data['os_name'],
                    'os_type': data['os_type'],
                    "security_group_ids": data['security_group_ids'],
                    "instance_network_type": data['instance_network_type'],
                    "internet_max_bandwidth_in": data['internet_max_bandwidth_in']+"Mbps",
                    "internet_max_bandwidth_out": data['internet_max_bandwidth_out']+"Mbps",
                    'disk_info': disk_info,
                    'image_info': image_info
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


class ServerPerformanceHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def post(self):
        """
        @api {post} /api/server/performance 主机性能
        @apiName ServerPerformanceHandler
        @apiGroup Server

        @apiParam {Number} id 主机ID
        @apiParam {Number} start_time 起始时间
        @apiParam {Number} end_time 终止时间
        @apiParam {Number} type 0: 机器详情 1: 正常 2: 按时平均 3: 按天平均
        @apiParam {Number} now_page 当前页面
        @apiParam {Number} page_number 每页返回条数， 小于100条

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "cpu": [
                        {"timestamp": str, "percent": int},
                        ...
                    ],
                    "memory": [
                        {"timestamp": str, "total": int, "available": int, "free": int, "percent": int},
                        ...
                    ],
                    "disk": [
                        {"timestamp": str, "total": int, "free": int, "percent": int},
                        ...
                    ],
                    "net": [
                        {"timestamp":str, "input": int, "output": int},
                        ...
                    ]
                }
            }
        :return:
        """
        with catch(self):
            data = yield self.server_service.get_performance(self.params)
            self.success(data)


class ServerUpdateHandler(BaseHandler):
    @require(RIGHT['modify_server_info'], service=SERVICE['s'])
    @coroutine
    def post(self):
        """
        @api {post} /api/server/update 主机信息更新
        @apiName ServerUpdateHandler
        @apiGroup Server

        @apiUse cidHeader

        @apiParam {Number} id 主机id
        @apiParam {String} name 主机名字

        @apiUse Success
        """
        with catch(self):
            data = yield self.server_operation_service.add(params={
                'user_id': self.current_user['id'],
                'object_id': self.params['id'],
                'object_type': OPERATION_OBJECT_STYPE['server'],
                'operation': SERVER_OPERATE_STATUS['change'],
                'operation_status': OPERATE_STATUS['fail'],
            })

            old_name = yield self.server_service.select(fields='id,name', ut=False, ct=False)
            old_name = [i['name'] for i in old_name if i['id'] != self.params['id']]
            if self.params['name'] in old_name:
                self.error(
                    status=ERR_TIP['server_name_repeat']['sts'],
                    message=ERR_TIP['server_name_repeat']['msg']
                )
                return

            yield self.server_service.update_server(self.params)

            yield self.server_operation_service.update(
                    sets={'operation_status': OPERATE_STATUS['success']},
                    conds={'id': data['id']}
            )

            self.success()


class ServerStopHandler(BaseHandler):
    @require(RIGHT['start_stop_server'], service=SERVICE['s'])
    @coroutine
    def get(self, id):
        """
        @api {get} /api/server/stop/(\d+) 停止主机
        @apiName ServerStopHandler
        @apiGroup Server

        @apiUse cidHeader

        @apiParam {Number} id 主机id

        @apiUse Success

        """
        with catch(self):
            data = yield self.server_operation_service.add(params={
                                                            'user_id': self.current_user['id'],
                                                            'object_id': id,
                                                            'object_type': OPERATION_OBJECT_STYPE['server'],
                                                            'operation': SERVER_OPERATE_STATUS['stop'],
                                                            'operation_status': OPERATE_STATUS['fail'],
                                                        })
            yield self.server_service.stop_server(id)
            yield self.server_operation_service.update(
                                                        sets={'operation_status': OPERATE_STATUS['success']},
                                                        conds={'id': data['id']}
                                                    )
            self.success()


class ServerStartHandler(BaseHandler):
    @require(RIGHT['start_stop_server'], service=SERVICE['s'])
    @coroutine
    def get(self, id):
        """
        @api {get} /api/server/start/(\d+) 开启主机
        @apiName ServerStartHandler
        @apiGroup Server

        @apiUse cidHeader

        @apiParam {Number} id 主机id

        @apiUse Success
        """
        with catch(self):
            data = yield self.server_operation_service.add(params={
                                                            'user_id': self.current_user['id'],
                                                            'object_id': id,
                                                            'object_type': OPERATION_OBJECT_STYPE['server'],
                                                            'operation': SERVER_OPERATE_STATUS['start'],
                                                            'operation_status': OPERATE_STATUS['fail'],
                                                        })
            yield self.server_service.start_server(id)
            yield self.server_operation_service.update(
                                                        sets={'operation_status': OPERATE_STATUS['success']},
                                                        conds={'id': data['id']}
                                                    )
            self.success()


class ServerRebootHandler(BaseHandler):
    @require(RIGHT['start_stop_server'], service=SERVICE['s'])
    @coroutine
    def get(self, id):
        """
        @api {get} /api/server/reboot/(\d+) 重启主机
        @apiName ServerRebootHandler
        @apiGroup Server

        @apiUse cidHeader

        @apiParam {Number} id 主机id

        @apiUse Success
        """
        with catch(self):
            data = yield self.server_operation_service.add(params={
                                                            'user_id': self.current_user['id'],
                                                            'object_id': id,
                                                            'object_type': OPERATION_OBJECT_STYPE['server'],
                                                            'operation': SERVER_OPERATE_STATUS['reboot'],
                                                            'operation_status': OPERATE_STATUS['fail'],
                                                        })
            yield self.server_service.reboot_server(id)
            yield self.server_operation_service.update(
                                                        sets={'operation_status': OPERATE_STATUS['success']},
                                                        conds={'id': data['id']}
                                                    )
            self.success()


class ServerStatusHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, instance_id):
        """
        @api {get} /api/server/([\w\W]+)/status 查询实例状态
        @apiName ServerStatusHandler
        @apiGroup Server

        @apiParam {Number} instance_id 实例id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": "Running"
            }
        """
        with catch(self):
            data = yield self.server_service.get_instance_status(instance_id)

            self.success(data)


class ServerContainerPerformanceHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def post(self):
        """
        @api {post} /api/server/container/performance 获取主机里面的各个docker容器使用情况
        @apiName ServerContainerPerformanceHandler
        @apiGroup Server

        @apiParam {Number} id 主机id
        @apiParam {String} container_name 容器名字
        @apiParam {Number} start_time 起始时间
        @apiParam {Number} end_time 终止时间
        @apiParam {Number} type 0: 机器详情 1: 正常 2: 按时平均 3: 按天平均
        @apiParam {Number} now_page 当前页面
        @apiParam {Number} page_number 每页返回条数， 小于100条

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "cpu": [
                         {},
                         ...
                    ],
                    "memory": [
                        {},
                        ...
                    ],
                    "disk": [
                        {},
                        ...
                    ],
                    "net":
                }
            }
        """
        with catch(self):
            data = yield self.server_service.get_docker_performance(self.params)
            self.success(data)


class ServerContainersHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def get(self, id):
        """
        @api {get} /api/server/containers/(\d+) 获取主机里面的docker容器列表
        @apiName ServerContainersHandler
        @apiGroup Server

        @apiParam {Number} id 主机id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    [
                        "1a050e4d7e43", # container id
                         "harbor-jobservice", # container name
                        "Up 3 weeks", # status
                        "2017-05-18 14:06:50 +0800 CST\n" # created_time
                    ],
                    ...
                ]
            }
        """
        try:
            data = yield self.server_service.get_containers({"server_id": str(id)})

            self.success(data)
        except:
            self.success()


class ServerContainersInfoHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def get(self, id, container_id):
        """
        @api {get} /api/server/([\w\W]+)/container/([\w\W]+) 获取主机容器信息
        @apiName ServerContainersInfoHandler
        @apiGroup Server

        @apiParam {Number} id 服务器id
        @apiParam {Number} container_id 容器id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                     ...
                }
            }
        """
        with catch(self):
            params = yield self.server_service.fetch_ssh_login_info({'server_id': id})
            server_name = yield self.server_service.select(fields='name', conds={'id': id}, ct=False, ut=False, one=True)
            params.update({'container_id': container_id, 'server_name': server_name['name']})
            data, err = yield self.server_service.get_container_info(params)
            if err:
                self.error(err)
            else:
                self.success(data)


class ServerContainerStartHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def post(self):
        """
        @api {post} /api/server/container/start 启动容器
        @apiName ServerContainerStartHandler
        @apiGroup Server

        @apiUse cidHeader

        @apiParam {Number} id 主机id
        @apiParam {String} container_id 容器id

        @apiUse Success
        """
        with catch(self):
            data = yield self.server_operation_service.add(params={
                'user_id': self.current_user['id'],
                'object_id': self.params['container_id'],
                'object_type': OPERATION_OBJECT_STYPE['container'],
                'operation': CONTAINER_OPERATE_STATUS['start'],
                'operation_status': OPERATE_STATUS['fail'],
            })

            yield self.server_service.start_container(self.params)

            yield self.server_operation_service.update(
                    sets={'operation_status': OPERATE_STATUS['success']},
                    conds={'id': data['id']}
            )
            self.success()


class ServerContainerStopHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def post(self):
        """
        @api {post} /api/server/container/stop 停止容器
        @apiName ServerContainerStopHandler
        @apiGroup Server

        @apiUse cidHeader

        @apiParam {Number} id 主机id
        @apiParam {String} container_id 容器id

        @apiUse Success
        """
        with catch(self):
            data = yield self.server_operation_service.add(params={
                'user_id': self.current_user['id'],
                'object_id': self.params['container_id'],
                'object_type': OPERATION_OBJECT_STYPE['container'],
                'operation': CONTAINER_OPERATE_STATUS['stop'],
                'operation_status': OPERATE_STATUS['fail'],
            })

            yield self.server_service.stop_container(self.params)

            yield self.server_operation_service.update(
                    sets={'operation_status': OPERATE_STATUS['success']},
                    conds={'id': data['id']}
            )

            self.success()


class ServerContainerDelHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def post(self):
        """
        @api {post} /api/server/container/del 删除容器
        @apiName ServerContainerDelHandler
        @apiGroup Server

        @apiUse cidHeader

        @apiParam {Number} id 主机id
        @apiParam {String} container_id 容器id

        @apiUse Success
        """
        with catch(self):
            data = yield self.server_operation_service.add(params={
                'user_id': self.current_user['id'],
                'object_id': self.params['container_id'],
                'object_type': OPERATION_OBJECT_STYPE['container'],
                'operation': CONTAINER_OPERATE_STATUS['delete'],
                'operation_status': OPERATE_STATUS['fail'],
            })

            yield self.server_service.del_container(self.params)

            yield self.server_operation_service.update(
                    sets={'operation_status': OPERATE_STATUS['success']},
                    conds={'id': data['id']}
            )
            self.success()


class OperationLogHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/log/operation 操作记录
        @apiName OperationHandler
        @apiGroup Server

        @apiParam {Number} object_type 对象类型
        @apiParam {Number} object_id 对象id

        @apiSuccessExample {json} Success-Response:
         HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "created_time": str,
                        "operation" : int 0:开机, 1:关机, 2:重启
                        "operation_status": int 0:成功, 1:失败
                        "user": str
                    }
                    ...
                ]
            }
        """
        with catch(self):
            data = yield self.server_operation_service.get_server_operation(self.params)
            self.success(data)


class SystemLoadHandler(BaseHandler):
    @require(service=SERVICE['s'])
    @coroutine
    def get(self, sid):
        """
        @api {get} /api/server/(\d+)/systemload 服务器负载
        @apiName SystemLoadHandler
        @apiGroup Server

        @apiParam {number} sid 服务器id

        @apiSuccessExample {json} Success-Response:
        HTTP/1.1 200 OK
        {
            "status": 0,
            "msg": "success",
            "data": {
                "date": "2018-03-08 14:23:30"
                "run_time": "6天6小时30分钟"
                "login_users": 1,
                "one_minute_load": 0.14
                "five_minute_load": 0.34
                "fifteen_minute_load:" 0.24
            }
        }
        """
        with catch(self):
            ip = yield self.server_service.fetch_public_ip(int(sid))
            info = json.loads(self.redis.hget(SERVERS_REPORT_INFO, ip))
            self.success(info['system_load'])


class ServerThresholdHandler(BaseHandler):
    @coroutine
    def get(self):
        """
        @api {get} /api/server/threshold 服务器临界值标准
        @apiName ServerThresholdHandler
        @apiGroup Server

        @apiSuccessExample {json} Success-Response:
        HTTP/1.1 200 OK
        {
            "status": 0,
            "msg": "success",
            "data": {
                // 各项阀值
                "cpu_threshold": int,
                "memory_threshold": int,
                "disk_threshold": int,
                "net_threshold": int,
                "block_threshold": int, // 磁盘io
            }
        }
        """
        with catch(self):
            data = {
                "cpu_threshold": THRESHOLD['CPU_THRESHOLD'],
                "memory_threshold": THRESHOLD['MEM_THRESHOLD'],
                "disk_threshold": THRESHOLD['DISK_THRESHOLD'],
                "net_threshold": THRESHOLD['NET_THRESHOLD'],
                "block_threshold": THRESHOLD['BLOCK_THRESHOLD']
            }
            self.success(data)


class ServerMontiorHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/server/monitor 服务器热图数据
        @apiName ServerMonitorHandler
        @apiGroup Server

        @apiSuccessExample {json} Success-Response:
        HTTP/1.1 200 OK
        {
            "status": 0,
            "msg": "success",
            "data": [
                {
                    "serverID": int,
                    "name": string,
                    "colorType": int,
                    "cpuUsageRate": float,
                    "memUsageRate": float,
                    "diskUsageRate": float,
                    "diskIO": string,
                    "networkUsage": float,
                }
            ]
        }
        """
        with catch(self):
            cid, uid = self.params.get('cid'), self.current_user['id']
            if not cid:
                sid = yield self.server_service.select(fields='id',conds={'lord': uid, 'form': FORM_PERSON}, ct=False, ut=False)
            else:
                try:
                    self.company_employee_service.check_admin(uid=uid, cid=cid)
                    sid = yield self.user_access_server_service.select(
                                                                fields='sid',
                                                                conds={'cid': cid},
                                                                ct=False, ut=False
                    )
                except:
                    sid = yield self.user_access_server_service.select(
                                                        fields='sid',
                                                        conds={'cid': cid, 'uid': uid},
                                                        ct=False, ut=False
                    )
            sids = [i['sid'] for i in sid]
            data = yield self.server_service.get_monitor_data(sids)
            self.success(data)
