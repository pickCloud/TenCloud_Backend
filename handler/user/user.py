__author__ = 'Jon'

import traceback
from handler.base import BaseHandler
from tornado.gen import coroutine, Task
from utils.general import validate_mobile, validate_auth_code, gen_random_digits
from utils.decorator import is_login
from utils.datetool import seconds_to_human
from constant import AUTH_CODE, SMS_TIMEOUT, COOKIE_EXPIRES_DAYS, AUTH_CODE_ERROR_COUNT, AUTH_CODE_ERROR_COUNT_LIMIT, \
                     AUTH_LOCK, AUTH_LOCK_TIMEOUT, AUTH_LOCK_TIP, AUTH_FAILURE_TIP, \
                     SMS_SENDING_LOCK, SMS_SENDING_LOCK_TIMEOUT, SMS_SENDING_LOCK_TIP
from setting import settings


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

            # 检查sms_sending_lock
            sms_sending_lock = SMS_SENDING_LOCK.format(mobile=mobile)

            has_lock = yield Task(self.redis.get, sms_sending_lock)
            if has_lock:
                self.error(SMS_SENDING_LOCK_TIP)
                return

            # 发送短信验证码
            auth_code = gen_random_digits()

            yield Task(self.redis.setex, sms_sending_lock, SMS_SENDING_LOCK_TIMEOUT, '1')
            result = yield self.sms_service.send(mobile, auth_code)

            if result.get('err'):
                self.error(result.get('err'))
                return

            # 设置验证码有效期
            yield Task(self.redis.setex, AUTH_CODE.format(mobile=mobile, auth_code=auth_code), SMS_TIMEOUT, '1')

            self.log.info('mobile: {mobile}, auth_code: {auth_code}'.format(mobile=mobile, auth_code=auth_code))
            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())


class NeedSMSMixin(BaseHandler):
    """ 需要手机验证码操作的基类
    """
    def initialize(self):
        self.auth_code_key = ''
        self.auth_lock_key = ''
        self.err_count_key = ''

    @coroutine
    def check(self, mobile, auth_code):
        # 检查auth_lock
        self.auth_lock_key = AUTH_LOCK.format(mobile=mobile)

        has_lock = yield Task(self.redis.get, self.auth_lock_key)
        if has_lock:
            self.error(AUTH_LOCK_TIP)
            return False

        # 认证
        self.auth_code_key = AUTH_CODE.format(mobile=mobile, auth_code=auth_code)
        self.err_count_key = AUTH_CODE_ERROR_COUNT.format(mobile=mobile)

        is_exist = yield Task(self.redis.get, self.auth_code_key)
        if not is_exist:
            err_count = yield Task(self.redis.get, self.err_count_key)
            err_count = int(err_count) if err_count else 0
            err_count += 1

            if err_count >= AUTH_CODE_ERROR_COUNT_LIMIT:
                yield Task(self.redis.setex, self.auth_lock_key, AUTH_LOCK_TIMEOUT, '1')
                yield Task(self.redis.delete, self.err_count_key)
                self.error(AUTH_LOCK_TIP)
            else:
                yield Task(self.redis.set, self.err_count_key, err_count)
                self.error(AUTH_FAILURE_TIP.format(count=err_count))

            return False

        return True

    @coroutine
    def clean(self):
        """ 清除auth_code && 登陆lock && 登陆错误次数
        """
        yield Task(self.redis.delete, self.auth_code_key, self.auth_lock_key, self.err_count_key)

class UserLoginHandler(NeedSMSMixin):
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

            is_ok = yield self.check(mobile, auth_code)

            if not is_ok: return

            # 现在的登陆模式是手机+验证码，所以首次登陆，则插入数据
            data = yield self.user_service.select(conds=['mobile=%s'], params=[mobile], one=True)
            if not data:
                yield self.user_service.add({'mobile': mobile})
                data = yield self.user_service.select(conds=['mobile=%s'], params=[mobile], one=True)

            # 设置cookie
            self.set_secure_cookie('user_id', str(data['id']), expires_days=COOKIE_EXPIRES_DAYS)

            # 设置session
            yield self.set_session(data['id'], data)

            yield self.clean()

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
                "email": str,
                "image_url": str,
            }

        @apiUse Success
        """
        try:
            old = self.current_user

            new = {
                'id': old['id'],
                'name': self.params.get('name', '') or old['name'],
                'email': self.params.get('email' '') or old['email'],
                'image_url': settings['qiniu_bucket_url'] + self.params.get('image_url', '') \
                             if self.params.get('image_url', '') else old['image_url'],
                'create_time': old['create_time'],
                'update_time': seconds_to_human()
            }

            yield self.user_service.update(sets=['name=%s', 'email=%s', 'image_url=%s'],
                                           conds=['id=%s'],
                                           params=[new['name'], new['email'], new['image_url'], new['id']])

            yield self.set_session(new['id'], new)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class UserUploadToken(BaseHandler):
    @is_login
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
                    "token": str,
                    "timeout": int,
                }
            }
        """
        try:
            data = yield self.user_service.get_qiniu_token()
            self.success(data)
        except:
            self.error()
            self.log.error(traceback.format_exc())