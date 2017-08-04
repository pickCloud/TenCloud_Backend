from service.base import BaseService
from tornado.concurrent import run_on_executor
from qiniu import Auth
from setting import settings

class UserService(BaseService):
    table = 'user'
    fields = 'id, mobile, email, name, image_url'

    @run_on_executor
    def get_qiniu_token(self):
        q = Auth(access_key=settings['qiniu_access_key'], secret_key=settings['qiniu_secret_key'])
        token = q.upload_token(bucket=settings['qiniu_bucket_name'], expires=settings['qiniu_token_timeout'])
        return {'token': token, 'timeout': settings['qiniu_token_timeout']}



