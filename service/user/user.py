from service.base import BaseService
from tornado.concurrent import run_on_executor
from tornado.gen import coroutine
from utils.sms import SMS
from constant import SMS_TIP
from qiniu import Auth
from setting import ACCESS_KEY, SECRET_KEY, BUCKET_NAME, TOKEN_TIMEOUT

class UserService(BaseService):
    table = 'user'
    fields = 'id, mobile, email, name, image_url'

    @run_on_executor
    def send_sms(self, mobile, code):

        result = SMS.send(to=mobile, body=SMS_TIP.format(code=code))

        return result

    @coroutine
    def get_qiniu_token(self):
        q = Auth(access_key=ACCESS_KEY, secret_key=SECRET_KEY)
        token = q.upload_token(bucket=BUCKET_NAME, expires=TOKEN_TIMEOUT)
        return token



