from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from constant import MAX_PAGE_NUMBER, RIGHT, SERVICE, PREDOWNLOAD_URL, FORM_PERSON, FORM_COMPANY


class FileListHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/file/list 文件分页
        @apiName FileListHandler
        @apiGroup File

        @apiUse cidHeader
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
            self.params.update(self.get_lord())
            data = yield self.file_service.seg_page(self.params)

            data = yield self.filter(data, service=SERVICE['f'], key='dir')

            # 进行分页处理
            start = (self.params['now_page'] - 1) * self.params['page_number']
            end = self.params['now_page'] * self.params['page_number']
            self.success(data[start:end] if data else [])


class FileTotalHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, file_id):
        """
        @api {get} /api/file/([\w\W]+)/pages 总页数
        @apiName FileTotal
        @apiGroup File

        @apiUse cidHeader
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
            params = self.get_lord()
            params.update({'pid': file_id})
            data = yield self.file_service.total_pages(params)
            self.success(data)


class FileInfoHandler(BaseHandler):
    @require(service=SERVICE['f'])
    @coroutine
    def get(self, id):
        """
        @api {get} /api/file/([\w\W]+) 文件详细信息
        @apiName FileInfo
        @apiGroup File

        @apiUse cidHeader
        @apiParam {Number} id 文件id

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
            data = yield self.file_service.select({'id': int(id)}, one=True)
            self.success(data)


class FileUploadHandler(BaseHandler):
    @require(RIGHT['upload_file'])
    @coroutine
    def post(self):
        """
        @api {post} /api/file/upload 文件上传
        @apiName FileUpload
        @apiGroup File

        @apiUse cidHeader

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
                patch = self.get_lord()
                arg.update(patch)
                arg.update({'owner': self.current_user['id']})
                data = yield self.file_service.batch_upload(arg)

                # 当上传文件不是个人文件时
                if self.params['cid'] != 1:
                    arg = {
                        'uid': self.current_user['id'],
                        'cid': self.params['cid'],
                        'fid': data['file_id']
                    }
                    yield self.user_access_filehub_service.add(arg)

                resp.append(data)
            self.success(resp)


class FileUpdateHandler(BaseHandler):
    @require(service=SERVICE['f'])
    @coroutine
    def post(self):
        """
        @api {post} /api/file/update 更新七牛返回的文件信息
        @apiName FileUpdate
        @apiGroup File

        @apiUse cidHeader

        @apiParam {Number} status 当为0时，下述字段不为空；为1时，代表上传失败，删除记录，除file_id外，其余为空
        @apiParam {Number} id 原为file_id
        @apiParam {Number} size
        @apiParam {String} mime
        @apiParam {String} qiniu_id

        @apiUse Success
        """
        with catch(self):
            fid = self.params['id']
            if self.params['status'] == 1:
                yield self.file_service.delete({'id': fid})
                if self.params.get('cid'):
                    yield self.user_access_filehub_service.delete({'fid': fid, 'cid': self.params['cid'], 'uid': self.current_user['id']})
                self.success()
                return

            sets = {
                'size': self.params.get('size'),
                'qiniu_id': self.params.get('qiniu_id'),
                'mime': self.params.get('mime')
            }
            yield self.file_service.update(sets=sets, conds={'id': fid, 'owner': self.current_user['id']})
            self.success()


class FileDownloadHandler(BaseHandler):
    @require(RIGHT['download_file'])
    @coroutine
    def get(self, file_id):
        """
        @api {get} /api/file/download/([\w\W+]) 文件下载
        @apiName FileDownload
        @apiGroup File

        @apiUse cidHeader

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


class FileDownloadPreHandler(BaseHandler):
    @require(RIGHT['download_file'])
    @coroutine
    def get(self, file_id):
        """
        @api {get} /api/file/predownload/([\w\W+]) 文件预下载
        @apiName FileDownload
        @apiGroup File

        @apiUse cidHeader

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 302 OK
            {
                'url': 'https://c.10.com/#/download?file_id=xxxxxx'
            }
        """
        with catch(self):
            url = PREDOWNLOAD_URL.format(file_id=file_id)
            self.success({'url':url})


class FileDirCreateHandler(BaseHandler):
    @require(RIGHT['add_directory'])
    @coroutine
    def post(self):
        """
        @api {post} /api/file/dir/create 创建目录
        @apiName FileDirCreate
        @apiGroup File

        @apiUse cidHeader

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
            lord = self.get_lord()
            arg = {
                'filename': self.params['dir_name'],
                'pid': self.params['pid'],
                'type': 1,
                'size': 0,
                'qiniu_id': '',
                'owner': self.current_user['id'],
                'mime': '',
                'hash': '',
                'lord': lord['lord'],
                'form': lord['form']
            }
            data = yield self.file_service.add(arg)
            resp = yield self.file_service.select(conds={'id': data['id']})

            # 获取父节点的绝对路径,用以生成当前目录的完整路径
            pdata = yield self.file_service.select(conds={'id': self.params['pid']}, one=True)
            pdir = (pdata.get('dir') if pdata else '/0') + '/' + str(data['id'])
            yield self.file_service.update(sets={'dir': pdir}, conds={'id': data['id']})
            self.success(resp)


class FileDeleteHandler(BaseHandler):
    @require(RIGHT['delete_file'], service=SERVICE['f'])
    @coroutine
    def post(self):
        """
        @api {post} /api/file/delete 文件删除
        @apiName FileDelete
        @apiGroup File

        @apiUse cidHeader

        @apiParam {Number} id file_ids改为id

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
            files = yield self.file_service.select(fields='id, owner, form',
                                                   conds={'id': self.params['id']},
                                                   ct=False, ut=False
                                                   )
            correct_ids = []
            incorrect_ids = []
            for file in files:
                if (file['form'] == FORM_PERSON and file['owner'] == self.current_user['id']) or file['form'] == FORM_COMPANY:
                    correct_ids.append(file['id'])
                    continue
                incorrect_ids.append(file['id'])

            if correct_ids:
                yield self.file_service.delete({'id': correct_ids})
            if incorrect_ids:
                self.error(data={'file_ids': incorrect_ids})
                return
            self.success()