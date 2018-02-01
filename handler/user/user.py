__author__ = 'Jon'

import traceback

from tornado.gen import Task, coroutine
from geetest import GeetestLib
import bcrypt
import json
from constant import AUTH_CODE, AUTH_CODE_ERROR_COUNT, AUTH_LOCK, AUTH_LOCK_TIMEOUT, \
    SMS_FREQUENCE_LOCK, SMS_FREQUENCE_LOCK_TIMEOUT, SMS_TIMEOUT, SMS_SENT_COUNT, SMS_SENT_COUNT_LIMIT, \
    SMS_SENT_COUNT_LIMIT_TIMEOUT, SMS_NEED_GEETEST_COUNT, ERR_TIP, AUTH_CODE_ERROR_COUNT_LIMIT, SMS_EXISTS_TIME, LOGOUT_CID
from handler.base import BaseHandler
from setting import settings
from utils.datetool import seconds_to_human
from utils.decorator import is_login
from utils.security import password_strength
from utils.general import gen_random_code, validate_auth_code, validate_mobile, validate_user_password
from utils.context import catch


"""
@apiDefine Login
@apiSuccessExample {json} Success-Response:
  HTTP/1.1 200 ok
    {
        "status": int,
        "message": str,
        "data": {
            "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MTI1NTAyMTMsImlhdCI6MTUxMTk0NTQxMywic3ViIjoxfQ.CmyWtufHH5jte3xFjvUPhiu_T2pv57qX6jxHyqju7Og",
            "cid": 0=>个人，其他=>公司
        }
    }
"""


class UserBase(BaseHandler):
    @coroutine
    def validate_captcha(self, challenge='', validate='', seccode=''):
        gt = GeetestLib(settings['gee_id'], settings['gee_key'])
        status = self.redis.get(gt.GT_STATUS_SESSION_KEY)
        if int(status) == 1:
            result = gt.success_validate(challenge, validate, seccode)
        else:
            result = gt.failback_validate(challenge, validate, seccode)
        if not result:
            return False
        return True


    def get_sms_count(self, mobile):
        # 检查手机一天的发送次数
        sms_sent_count_key = SMS_SENT_COUNT.format(mobile=mobile)
        sms_sent_count = self.redis.get(sms_sent_count_key)
        sms_sent_count = int(sms_sent_count) if sms_sent_count else 0
        return sms_sent_count


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

        has_lock = self.redis.get(self.auth_lock_key)
        if has_lock:
            self.error(
                status=ERR_TIP['auth_code_many_errors']['sts'],
                message=ERR_TIP['auth_code_many_errors']['msg']
            )
            return False

        # 认证
        self.auth_code_key = AUTH_CODE.format(mobile=mobile)
        self.err_count_key = AUTH_CODE_ERROR_COUNT.format(mobile=mobile)

        # 验证码超时
        code_ttl = self.redis.ttl(self.auth_code_key)
        if 0 < code_ttl < SMS_EXISTS_TIME-SMS_TIMEOUT:
            self.error(status=ERR_TIP['auth_code_timeout']['sts'], message=ERR_TIP['auth_code_timeout']['msg'])
            return False

        real_code = self.redis.get(self.auth_code_key)

        if auth_code != real_code:
            err_count = self.redis.get(self.err_count_key)
            err_count = int(err_count) if err_count else 0
            err_count += 1

            if err_count >= AUTH_CODE_ERROR_COUNT_LIMIT:
                self.redis.setex(self.auth_lock_key, AUTH_LOCK_TIMEOUT, '1')
                self.redis.delete(self.err_count_key)
                self.error(
                    status=ERR_TIP['auth_code_many_errors']['sts'],
                    message=ERR_TIP['auth_code_many_errors']['msg']
                )
            else:
                self.redis.setex(self.err_count_key, SMS_SENT_COUNT_LIMIT_TIMEOUT, err_count)
                self.error(
                        status=ERR_TIP['auth_code_has_error']['sts'],
                        message=ERR_TIP['auth_code_has_error']['msg'].format(count=err_count),
                )

            return False

        return True

    def clean(self):
        """ 清除auth_code && 登陆lock && 登陆错误次数
        """
        self.redis.delete(self.auth_code_key, self.auth_lock_key, self.err_count_key)


class UserSMSHandler(UserBase):
    @coroutine
    def post(self):
        """
        @api {post} /api/user/sms 发送手机验证码
        @apiName UserSMSHandler
        @apiGroup User

        @apiParam {String} mobile
        @apiParam {String} geetest_challenge
        @apiParam {String} geetest_validate
        @apiParam {String} geetest_seccode

        @apiSuccessExample {json} Success-Response:
          HTTP/1.1 200 ok
            {
                "sms_count": int
            }
        """
        with catch(self):
            mobile = self.params['mobile']
            # 参数认证
            validate_mobile(mobile)

            # 检查手机一分钟只能发送一次锁
            sms_frequence_lock = SMS_FREQUENCE_LOCK.format(mobile=mobile)

            has_lock = self.redis.get(sms_frequence_lock)
            if has_lock:
                self.error(status=ERR_TIP['sms_too_frequency']['sts'], message=ERR_TIP['sms_too_frequency']['msg'])
                return

            sms_sent_count_key = SMS_SENT_COUNT.format(mobile=mobile)
            sms_sent_count = self.get_sms_count(mobile)

            data = {
                'sms_count': sms_sent_count,
            }

            if sms_sent_count >= SMS_SENT_COUNT_LIMIT:
                self.error(status=ERR_TIP['sms_over_limit']['sts'], message=ERR_TIP['sms_over_limit']['msg'], data=data)
                return

            if sms_sent_count >= SMS_NEED_GEETEST_COUNT:
                challenge = self.params.get('geetest_challenge', '')
                if not challenge:
                    self.error(status=ERR_TIP['sms_over_three']['sts'], message=ERR_TIP['sms_over_three']['msg'], data=data)
                    return
                valid = yield self.validate_captcha(
                    challenge=self.params['geetest_challenge'],
                    seccode=self.params['geetest_seccode'],
                    validate=self.params['geetest_validate']
                )
                if not valid:
                    self.error(status=ERR_TIP['fail_in_geetest']['sts'], message=ERR_TIP['sms_over_three']['msg'])
                    return

            # 发送短信验证码
            auth_code = gen_random_code()

            self.redis.setex(sms_frequence_lock, SMS_FREQUENCE_LOCK_TIMEOUT, '1')
            result = yield self.sms_service.send(mobile, auth_code)

            if result.get('err'):
                self.error(result.get('err'))
                return

            # 增加手机发送次数
            if sms_sent_count == 0:
                self.redis.setex(sms_sent_count_key, SMS_SENT_COUNT_LIMIT_TIMEOUT, '1')
            else:
                self.redis.incr(sms_sent_count_key)

            # 设置验证码有效期
            self.redis.setex(AUTH_CODE.format(mobile=mobile), SMS_EXISTS_TIME, auth_code)

            self.log.info('mobile: {mobile}, auth_code: {auth_code}'.format(mobile=mobile, auth_code=auth_code))

            data['sms_count'] = sms_sent_count +1
            self.success(data)


class GetCaptchaHandler(BaseHandler):
    def get(self):
        """
        @api {get} /api/user/captcha 极验证验证码预处理
        @apiName GetCaptChaHandler
        @apiGroup User

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": {
                    "success": int,
                    "gt": str,
                    "challenge": str,
                    "new_captcha": boolean
                }
            }
        """
        with catch(self):
            gt = GeetestLib(settings['gee_id'], settings['gee_key'])
            status = gt.pre_process()
            if not status:
                status = 2
            self.redis.set(gt.GT_STATUS_SESSION_KEY, status)
            response_str = json.loads(gt.get_response_str())
            self.success(response_str)


class UserReturnSMSCountHandler(UserBase):
    def get(self, mobile):
        """
        @api {get} /api/user/sms/(\d+)/count 验证码次数查询
        @apiName UserReturnSMSCountHandler
        @apiGroup User

        @apiParam {Number} mobile

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
                {
                    "status": 0,
                    "message": "success",
                    "data": {
                        "sms_count": int
                    }
                }
        """
        with catch(self):
            mobile = int(mobile)
            sms_sent_count = self.get_sms_count(mobile)

            data = {
                'sms_count': sms_sent_count,
            }

            self.success(data)


class UserSmsSetHandler(BaseHandler):
    """ tmp api for test
    """
    @is_login
    def get(self, count):
        with catch(self):
            sms_sent_count_key = SMS_SENT_COUNT.format(mobile=self.current_user['mobile'])
            self.redis.setex(sms_sent_count_key, SMS_SENT_COUNT_LIMIT_TIMEOUT, str(count))
            self.success()
            self.log.stats('Logout, IP: {}, Mobile: {}'.format(self.request.headers.get("X-Real-IP") or self.request.remote_ip, self.current_user['mobile']))


class UserDeleteHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        with catch(self):
            self.del_session(self.current_user['id'])
            yield self.user_service.delete(conds=['id=%s'], params=[self.current_user['id']])
            self.success()

            self.log.stats('Logout, IP: {}, Mobile: {}'.format(self.request.headers.get("X-Real-IP") or self.request.remote_ip, self.current_user['mobile']))


class UserDetailHandler(BaseHandler):
    @is_login
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
                    "gender": int,
                    "birthday": int
                }
            }
        """
        with catch(self):
            self.success(self.current_user)


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
                "mobile": str,
                "gender": int,
                "birthday": int
            }

        @apiUse Success
        """
        with catch(self):
            old = self.current_user

            new = {
                'id': old['id'],
                'name': self.params.get('name', '') or old.get('name', ''),
                'email': self.params.get('email', '') or old.get('email', ''),
                'image_url': settings['qiniu_header_bucket_url'] + self.params.get('image_url', '') \
                             if self.params.get('image_url', '') else old.get('image_url', ''),
                'mobile': self.params.get('mobile', '') or old.get('mobile', ''),
                'create_time': old['create_time'],
                'update_time': seconds_to_human(),
                "gender": self.params.get('gender') or int(old.get('gender', 3)),
                'birthday': self.params.get('birthday') or int(old.get('birthday', 0))
            }

            sets = {
                'name': new['name'],
                'email': new['email'],
                'image_url': new['image_url'],
                'mobile': new['mobile'],
                'gender': new['gender'],
                'birthday': new['birthday']
            }

            yield self.user_service.update(sets=sets,
                                           conds={'id': new['id']}
                                           )

            self.set_session(new['id'], new)

            self.success()


class UserUploadToken(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/user/token 获取七牛的上传token
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
        with catch(self):
            data = yield self.user_service.get_qiniu_token()
            self.success(data)

    @is_login
    def delete(self):
        """
        @api {delete} /api/user/token 用户删除git token
        @apiName UserDeleteToken
        @apiGroup User

        @apiUse Success
        """
        with catch(self):
            self.user_service.delete_token(self.current_user['id'])
            self.success()


class FileUploadMixin(BaseHandler):
    def get_file_info(self, param='file'):
        """
        :param param: 前端上传的参数名
        :return 文件名, 文件内容
        """
        if len(self.request.files) == 0:
            filename, content = self.params['param'], self.request.body
        else:
            filename, content = self.request.files[param][0]['filename'], self.request.files[param][0]['body']

        return filename, content

    @coroutine
    def handle_file_upload(self, new_name=None):
        filename, content = self.get_file_info()

        self.log.info('---FileUpload--- filename: %s, new_name: %s, content_len: %s' % (filename, new_name, len(content)))

        filename = yield self.user_service.save_file(new_name or filename, content)

        return filename


#########################################################################################################################
# 注册，登录，登出
#########################################################################################################################
class UserRegisterHandler(NeedSMSMixin, UserBase):
    @coroutine
    def post(self):
        """
        @api {post} /api/user/register 用户注册
        @apiName  UserRegisterHandler
        @apiGroup User

        @apiParam {Number} mobile 手机号码
        @apiParam {String} auth_code 验证码
        @apiParam {String} password 密码

        @apiSuccessExample {json} Success-Response:
          HTTP/1.1 200 ok
            {
                "status": int,
                "message": str,
                "data": {
                    "token": 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE1MTI1NTAyMTMsImlhdCI6MTUxMTk0NTQxMywic3ViIjoxfQ.CmyWtufHH5jte3xFjvUPhiu_T2pv57qX6jxHyqju7Og'
                }
            }
        """
        with catch(self):
            args = ['mobile', 'auth_code', 'password']

            self.guarantee(*args)
            self.strip(*args)

            validate_mobile(self.params['mobile'])
            validate_auth_code(self.params['auth_code'])
            validate_user_password(self.params['password'])

            data = yield self.user_service.select(fields='id',
                                                  conds={'mobile': self.params['mobile']},
                                                  ct=False, ut=False, one=True
                                                 )
            if data:
                self.error(status=ERR_TIP['mobile_has_exist']['sts'],message=ERR_TIP['mobile_has_exist']['msg'])
                return

            mobile, auth_code = self.params['mobile'], self.params['auth_code']
            is_ok = yield self.check(mobile, auth_code)
            if not is_ok:
                return

            arg = {
                'mobile': mobile,
                'password_strength': password_strength(self.params['password'])
            }
            yield self.user_service.add(params=arg)

            result = yield self.make_session(self.params['mobile'], set_token=True)
            self.clean()
            result['user'] = arg
            self.success(result)


class PasswordLoginHandler(UserBase):
    @coroutine
    def post(self):
        """
        @api {post} /api/user/login/password 密码登录
        @apiName PasswordLoginHandler
        @apiGroup User

        @apiParam {String} mobile 手机号码
        @apiParam {String} password 密码

        @apiUse Login
        """
        with catch(self):
            args = ['mobile', 'password']

            self.guarantee(*args)
            self.strip(*args)

            validate_mobile(self.params['mobile'])
            validate_user_password(self.params['password'])

            password = self.params['password'].encode('utf-8')

            data = yield self.user_service.select({'mobile': self.params['mobile']}, one=True)
            if not data:
                self.error(status=ERR_TIP['no_registered']['sts'], message=ERR_TIP['no_registered']['msg'])
                return

            hashed = data['password'].encode('utf-8')

            if hashed and bcrypt.checkpw(password, hashed):
                result = yield self.make_session(self.params['mobile'], set_token=True)

                cid = self.redis.hget(LOGOUT_CID, self.params['mobile'])

                result['cid'] = int(cid) if cid else 0

                data.pop('password', None)
                result['user'] = data
                self.success(result)
            else:
                self.error(status=ERR_TIP['password_error']['sts'], message=ERR_TIP['password_error']['msg'])

            self.log.stats('PasswordLogin, IP: {}, Mobile: {}'.format(self.request.headers.get("X-Real-IP") or self.request.remote_ip, self.params['mobile']))


class UserLoginHandler(NeedSMSMixin, UserBase):
    @coroutine
    def post(self):
        """
        @api {post} /api/user/login 验证码登陆
        @apiName UserLoginHandler
        @apiGroup User

        @apiParam {String} mobile
        @apiParam {String} auth_code


        @apiUse Login
        """
        with catch(self):
            # 参数认证
            args = ['mobile', 'auth_code']

            self.guarantee(*args)
            self.strip(*args)

            validate_mobile(self.params['mobile'])
            validate_auth_code(self.params['auth_code'])

            mobile, auth_code = self.params['mobile'], self.params['auth_code']

            is_ok = yield self.check(mobile, auth_code)
            if not is_ok:
                return

            result = yield self.make_session(self.params['mobile'], set_token=True)

            cid = self.redis.hget(LOGOUT_CID, self.params['mobile'])

            result['cid'] = int(cid) if cid else 0

            self.clean()

            user = yield self.user_service.select({'mobile': mobile}, one=True)
            user.pop('password', None)
            result['user'] = user
            if not user['password']:
                self.error(status=ERR_TIP['no_registered_jump']['sts'],
                           message=ERR_TIP['no_registered_jump']['msg'], data=result)
                return

            self.success(result)
            self.log.stats('AuthcodeLogin, IP: {}, Mobile: {}'.format(
                self.request.headers.get("X-Real-IP") or self.request.remote_ip, self.params['mobile']))

class UserLogoutHandler(BaseHandler):
    @is_login
    def post(self):
        """
        @api {post} /api/user/logout 用户退出
        @apiName UserLogoutHandler
        @apiGroup User

        @apiParam {Number} cid

        @apiUse Success
        """
        with catch(self):
            self.redis.hset(LOGOUT_CID, self.current_user['mobile'], self.params.get('cid', 0))

            self.del_session(self.current_user['id'])

            self.success()

            self.log.stats('Logout, IP: {}, Mobile: {}'.format(
                self.request.headers.get("X-Real-IP") or self.request.remote_ip, self.current_user['mobile']))


#########################################################################################################################
# 修改密码
#########################################################################################################################
class UserResetPasswordHandler(NeedSMSMixin, UserBase):
    @coroutine
    def post(self):
        """
           @api {post} /api/user/password/reset 重置密码
           @apiName UserResetPasswordHandler
           @apiGroup User

           @apiParam {String} mobile
           @apiParam {String} old_password
           @apiParam {String} new_password
           @apiParam {String} auth_code 验证码

           @apiUse Success
           """
        with catch(self):
            args = ['mobile', 'new_password', 'auth_code']
            self.guarantee(*args)
            self.strip(*args)

            validate_mobile(self.params['mobile'])
            validate_auth_code(self.params['auth_code'])
            validate_user_password(self.params['new_password'])

            mobile, auth_code = self.params['mobile'], self.params['auth_code']
            is_ok = yield self.check(mobile, auth_code)
            if not is_ok:
                return

            old_password = self.params.get('old_password', '')
            if old_password:
                old_password = old_password.encode('utf-8')
                hashed = yield self.user_service.select(
                    fields='password',
                    conds={'mobile': self.params['mobile']},
                    ct=False, ut=False, one=True
                )
                result = bcrypt.checkpw(old_password, hashed['password'].encode('utf-8'))
                if not result:
                    self.error(status=ERR_TIP['password_error']['sts'], message=ERR_TIP['password_error']['msg'])
                    return

            hashed = bcrypt.hashpw(self.params['new_password'].encode('utf-8'), bcrypt.gensalt())
            p_strength = password_strength(self.params['new_password'])
            yield self.user_service.update(
                                            sets={'password': hashed, 'password_strength': p_strength},
                                            conds={'mobile': self.params['mobile']}
            )
            yield self.make_session(self.params['mobile'])

            self.clean()

            self.success()


class UserPasswordSetHandler(UserBase):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/user/password/set 设置密码
        @apiName UserPasswordSetHandler
        @apiGroup User

        @apiParam {String} password

        @apiUse Success
        """
        with catch(self):
            password = self.params['password'].encode('utf-8')
            hashed = bcrypt.hashpw(password, bcrypt.gensalt())
            p_strength = password_strength(self.params['password'])
            yield self.user_service.update(
                sets={'password': hashed, 'password_strength': p_strength},
                conds={'id': self.current_user['id']}
            )
            yield self.make_session(self.current_user['mobile'])
            self.success()