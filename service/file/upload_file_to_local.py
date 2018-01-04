import os
from tornado.concurrent import run_on_executor
from service.base import BaseService
from setting import settings


class UploadImage(BaseService):
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