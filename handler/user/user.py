__author__ = 'Jon'

import traceback
from handler.base import BaseHandler
from tornado.gen import coroutine, Task
from utils.general import validate_mobile, validate_auth_code, gen_random_digits
from utils.decorator import is_login
from utils.datetool import seconds_to_human
from constant import AUTH_CODE, SMS_TIMEOUT, COOKIE_EXPIRES_DAYS, AUTH_CODE_ERROR_COUNT, AUTH_CODE_ERROR_COUNT_LIMIT, \
                     LOGIN_LOCK, LOGIN_LOCK_TIMEOUT, SMS_LOCK, SMS_LOCK_TIMEOUT, SMS_LOCK_TIP


class UserSMSHandler(BaseHandler):
    @coroutine
    def post(self, mobile):
        """
        @api {post} /api/user/sms/:mobile 发送验证码
        @apiName UserSMSHandler
        @apiGroup User

        @apiUse Success
        """
        try:
            # 参数认证
            validate_mobile(mobile)

            # 检查sms_lock
            sms_lock_key = SMS_LOCK.format(mobile=mobile)

            has_lock = yield Task(self.redis.get, sms_lock_key)
            if has_lock:
                self.error('一分钟内一个手机只能发送一次')
                return

            # 发送短信验证码
            auth_code = gen_random_digits()

            yield Task(self.redis.setex, sms_lock_key, SMS_LOCK_TIMEOUT, '1')
            result = yield self.user_service.send_sms(mobile, auth_code)

            if result.get('err'):
                self.error(result.get('err'))
                return

            # 保存auth_code
            yield Task(self.redis.setex, AUTH_CODE.format(mobile=mobile, auth_code=auth_code), SMS_TIMEOUT, '1')

            self.log.info('mobile: {mobile}, auth_code: {auth_code}'.format(mobile=mobile, auth_code=auth_code))
            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class UserLoginHandler(BaseHandler):
    @coroutine
    def post(self):
        """
        @api {post} /api/user/login 用户登陆
        @apiName UserLoginHandler
        @apiGroup User

        @apiParamExample {json} Request-Example:
            {
                "mobile": str
                "auth_code": str
            }

        @apiUse Success
        """
        try:
            # 参数认证
            args = ['mobile', 'auth_code']

            self.guarantee(*args)
            self.strip(*args)

            validate_mobile(self.params['mobile'])
            validate_auth_code(self.params['auth_code'])

            mobile, auth_code = self.params['mobile'], self.params['auth_code']

            # 检查login_lock
            login_lock_key = LOGIN_LOCK.format(mobile=mobile)

            has_lock = yield Task(self.redis.get, login_lock_key)
            if has_lock:
                self.error(SMS_LOCK_TIP)
                return

            # auth_code真实性
            auth_code_key = AUTH_CODE.format(mobile=mobile, auth_code=auth_code)
            err_count_key = AUTH_CODE_ERROR_COUNT.format(mobile=mobile)

            is_exist = yield Task(self.redis.get, auth_code_key)
            if not is_exist:
                err_count = yield Task(self.redis.get, err_count_key)
                err_count = int(err_count) if err_count else 0
                err_count += 1

                if err_count >= AUTH_CODE_ERROR_COUNT_LIMIT:
                    yield Task(self.redis.setex, login_lock_key, LOGIN_LOCK_TIMEOUT, '1')
                    yield Task(self.redis.delete, err_count_key)
                    self.error(SMS_LOCK_TIP)
                else:
                    yield Task(self.redis.set, err_count_key, err_count)
                    self.error('登陆验证码错误{count}次'.format(count=err_count))

                return

            # 现在的登陆模式是手机+验证码，所以首次登陆，则插入数据
            data = yield self.user_service.select(conds=['mobile=%s'], params=[mobile], one=True)
            if not data:
                yield self.user_service.add({'mobile': mobile})
                data = yield self.user_service.select(conds=['mobile=%s'], params=[mobile], one=True)

            # 设置cookie
            self.set_secure_cookie('user_id', str(data['id']), expires_days=COOKIE_EXPIRES_DAYS)

            # 设置session
            yield self.set_session(data['id'], data)

            # 清除auth_code && 登陆错误次数
            yield Task(self.redis.delete, auth_code_key, login_lock_key, err_count_key)

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class UserLogoutHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/user/logout 用户退出
        @apiName UserLogoutHandler
        @apiGroup User

        @apiUse Success
        """
        try:
            yield self.del_session(self.current_user['id'])
            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())



class UserDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/user 获取用户详情
        @apiName UserDetailHandler
        @apiGroup User

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": {
                    "id": int,
                    "name": str,
                    "mobile": str,
                    "email": str,
                    "image_url": str,
                    "create_time": str,
                    "update_time": str,
                }
            }
        """
        try:
            self.success(self.current_user)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class UserUpdateHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/user/update 更新用户信息
        @apiName UserUpdateHandler
        @apiGroup User

        @apiParamExample {json} Request-Example:
            {
                "name": str,
                "mobile": str,
                "email": str,
                "image_url": str,
            }

        @apiUse Success
        """
        try:
            old = self.current_user

            new = {
                'id': old['id'],
                'name': self.params.get('name') or old['name'],
                'mobile': self.params.get('mobile') or old['mobile'],
                'email': self.params.get('email') or old['email'],
                'image_url': self.params.get('image_url') or old['image_url'],
                'create_time': old['create_time'],
                'update_time': seconds_to_human()
            }

            yield self.user_service.update(sets=['name=%s', 'mobile=%s', 'email=%s', 'image_url=%s'],
                                           conds=['id=%s'],
                                           params=[new['name'], new['mobile'], new['email'], new['image_url'], new['id']]
                                           )

            yield self.set_session(new['id'], new)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class UserUploadToken(BaseHandler):
    @coroutine
    def get(self):
        """
        @api {get} /api/user/token 用户上传token
        @apiName UserUploadToken
        @apiGroup User

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": {
                    "token": str
                }
            }
        """
        try:
            token = yield self.user_service.get_qiniu_token()
            self.success({'token': token})
        except:
            self.error()
            self.log.error(traceback.format_exc())