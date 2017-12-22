import traceback

from tornado.gen import coroutine
from tornado.web import authenticated
from handler.base import BaseHandler
from utils.decorator import is_login
from utils.general import get_in_formats
from utils.context import catch
from constant import MAX_PAGE_NUMBER


class FileListHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/file/list 文件分页
        @apiName FileListHandler
        @apiGroup File

        @apiParam {Number} file_id
        @apiParam {Number} now_page 当前页面
        @apiParam {Number} page_number 每页返回条数，小于100条

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": [
                        {
                            "id": int,
                            "filename": str,
                            "size": str,
                            "qiniu_id": str,
                            "owner": str,
                            "mime": str,
                            "hash": str,
                            "type": int, 0为文件，1为文件夹， 当为1时，部分字段为空
                            "pid": int,
                            "url": str,
                            "thumb":str,
                            "create_time": str,
                            "update_time": str,
                        }
                            ...
                    ]
            }
        """
        with catch(self):
            if self.params['page_number'] > MAX_PAGE_NUMBER:
                self.error(message='over limit page number')
                return
            data = yield self.file_service.seg_page(self.params)
            self.success(data)


class FileTotalHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, file_id):
        """
        @api {get} /api/file/([\w\W]+)/pages 总页数
        @apiName FileTotal
        @apiGroup File

        @apiParam {Number} file_id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "successs",
                "data": int
            }
        """
        with catch(self):
            data = yield self.file_service.total_pages(file_id)
            self.success(data)


class FileInfoHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, file_id):
        """
        @api {get} /api/file/([\w\W]+) 文件详细信息
        @apiName FileInfo
        @apiGroup File

        @apiParam {Number} file_id 文件id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": {
                    "id": int,
                    "filename": str,
                    "size": str,
                    "qiniu_id": str,
                    "owner": str,
                    "mime": str,
                    "hash": str,
                    "type": int, 0为文件，1为文件夹， 当为1时，部分字段为空
                    "pid": int,
                    "url": str
                    "create_time": str,
                    "update_time": str,
                }
            }
        """
        with catch(self):
            data = yield self.file_service.select({'id': int(file_id)}, one=True)
            self.success(data)


class FileUploadHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/file/upload 文件上传
        @apiName FileUpload
        @apiGroup File

        @apiParam {String} filename 文件名
        @apiParam {String} hash 文件hash
        @apiParam {Number} pid 上一级目录id
        @apiParamExample {json} Request-Example:
            {
                file_infos: [
                    {
                        "filename": str,
                        "hash": str,
                        "pid": int,
                    }
                    ...
                ]
            }

         @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK:
            {
                "status": 0,
                "message": "success",
                "data": [
                    {
                        "file_status": int 文件状态，0:未存在，1:已存在
                        "file_id": int,
                        "token": str, 当file_status为1时，为空字段
                    }
                        ...
                ]
            }
        """
        with catch(self):
            resp = []
            for arg in self.params['file_infos']:
                arg.update({'owner': self.current_user['id']})
                data = yield self.file_service.batch_upload(arg)
                resp.append(data)
            self.success(resp)


class FileUpdateHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/file/update 更新七牛返回的文件信息
        @apiName FileUpdate
        @apiGroup File

        @apiParam {Number} status 当为0时，下述字段不为空；为1时，代表上传失败，删除记录，除file_id外，其余为空
        @apiParam {Number} file_id
        @apiParam {Number} size
        @apiParam {String} mime
        @apiParam {String} qiniu_id

        @apiUse Success
        """
        with catch(self):
            if self.params['status'] == 1:
                yield self.file_service.delete({'id': self.params['file_id']})
                self.success()
                return

            yield self.file_service.update(sets={
                                                'size': self.params.get('size'),
                                                'qiniu_id': self.params.get('qiniu_id'),
                                                'mime': self.params.get('mime')
                                            },
                                            conds={'id': self.params['file_id'], 'owner': self.current_user['id']},
                                        )
            self.success()


class FileDownloadHandler(BaseHandler):
    @authenticated
    @coroutine
    def get(self, file_id):
        """
        @api {get} /api/file/download/([\w\W+]) 文件下载
        @apiName FileDownload
        @apiGroup File

        @apiParam {Number} file_id 文件id

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 302 OK
            {
              跳转到七牛下载页面
            }
        """
        with catch(self):
            url = yield self.file_service.private_download_url(qiniu_id=file_id)
            self.redirect(url=url, permanent=False, status=302)


class FileDirCreateHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/file/dir/create 创建目录
        @apiName FileDirCreate
        @apiGroup File

        @apiParam {Number} pid 上一级目录id
        @apiParam {String} dir_name 目录名字

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "message": "success",
                "data": {
                    "id": int,
                    "filename": str,
                    "size": str,
                    "qiniu_id": str,
                    "owner": str,
                    "mime": str,
                    "hash": str,
                    "type": int, 0为文件，1为文件夹， 当为1时，部分字段为空
                    "pid": int,
                    "url: str,
                    "create_time": str,
                    "update_time": str,
                }
            }
        """
        with catch(self):
            arg = {
                'filename': self.params['dir_name'],
                'pid': self.params['pid'],
                'type': 1,
                'size': 0,
                'qiniu_id': '',
                'owner': self.current_user['id'],
                'mime': '',
                'hash': '',
            }
            data = yield self.file_service.add(arg)
            resp = yield self.file_service.select(conds={'id': data['id']})
            self.success(resp)


class FileDeleteHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/file/delete 文件删除
        @apiName FileDelete
        @apiGroup File

        @apiParam {Number} file_ids

        @apiSuccessExample {json} Success-Example:
            HTTP/1.1 200 OK
            {
                 "status": 0,
                "message": "success",
                "data": {
                    "file_ids": []int,
                }
            }
        """
        with catch(self):
            files = yield self.file_service.select(fields='id, owner',
                                                   conds={'id': self.params['file_ids']},
                                                   ct=False, ut=False
                                                   )
            correct_ids = []
            incorrect_ids = []
            for file in files:
                if file['owner'] == self.current_user['id']:
                    correct_ids.append(file['id'])
                    continue
                incorrect_ids.append(file['id'])

            if correct_ids:
                yield self.file_service.delete({'id': correct_ids})
            if incorrect_ids:
                self.error(data={'file_ids': incorrect_ids})
                return
            self.success()