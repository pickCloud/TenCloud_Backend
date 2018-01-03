from tornado.gen import coroutine

from handler.base import BaseHandler


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