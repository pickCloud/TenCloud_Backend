import os
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


    @run_on_executor
    def save_file(self, filename=None, content=None, path=settings['store_path']):
        """
        :param filename: 文件上传后的存储名 e.g. 123.tar
        :param path:     上传文件的存储路径 e.g. /file/store
        :return:  文件名
        """
        if not filename or content is None:
            raise ValueError('请输入文件名或文件内容')

        if not os.path.exists(path): os.makedirs(path)

        filepath = os.path.join(path, filename)

        with open(filepath, 'wb') as up:
            up.write(content)

        return filename
