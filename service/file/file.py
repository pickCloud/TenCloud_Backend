
from qiniu import Auth
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor
from service.base import BaseService
from constant import QINIU_POLICY, FULL_DATE_FORMAT, UPLOAD_STATUS
from setting import settings


class FileService(BaseService):
    table = 'filehub'
    fields = 'id, filename, size, qiniu_id, owner, mime, hash, type, pid, url, upload_status'

    def __init__(self, ak, sk):
        super().__init__()
        self.qiniu = Auth(access_key=ak, secret_key=sk)

    @run_on_executor
    def upload_token(self):
        policy = QINIU_POLICY
        expires = settings['qiniu_token_timeout']
        bucket = settings['qiniu_file_bucket']
        token = self.qiniu.upload_token(bucket=bucket, expires=expires, policy=policy)
        return token

    @run_on_executor
    def private_download_url(self, qiniu_id):
        url = settings['qiniu_file_bucket_url']+'/'+qiniu_id
        expires = settings['qiniu_token_timeout']
        download_url = self.qiniu.private_download_url(url=url, expires=expires)
        return download_url

    @coroutine
    def check_file_exist(self, hash):
        sql = "SELECT filename, size, qiniu_id, mime, upload_status, url FROM {table} WHERE hash=%s".format(table=self.table)
        cur = yield self.db.execute(sql, [hash])
        return cur.fetchone()

    @coroutine
    def batch_upload(self, params):
        arg = {
            'filename': '',
            'size': 0,
            'qiniu_id': '',
            'owner': params['owner'],
            'mime': '',
            'hash': params['hash'],
            'type': 0,
            'pid': params['pid'],
            'upload_status': UPLOAD_STATUS['unupload'],
            'url': ''
        }
        resp = {'file_status': 0, 'token': '', 'file_id': ''}
        data = yield self.check_file_exist(params['hash'])
        if data:
            resp['file_status'] = 1
            arg['filename'] = data['filename']
            arg['size'] = data['size']
            arg['qiniu_id'] = data['qiniu_id']
            arg['mime'] = data['mime']
            arg['upload_status'] = data['upload_status']
            arg['url'] = data['url']
        else:
            resp['token'] = yield self.upload_token()
        add_result = yield self.add(arg)
        resp['file_id'] = add_result['id']
        return resp

    @coroutine
    def seg_page(self, params):
        sql = """
                SELECT f.id, f.filename, f.size, f.qiniu_id, u.name, f.mime, f.hash, f.type, f.pid, f.url, f.upload_status, 
                DATE_FORMAT(f.create_time, %s ) as create_time, DATE_FORMAT(f.update_time, %s) as update_time 
                FROM {filehub} as f, {user} as u
                WHERE f.pid = %s AND f.upload_status = %s AND f.owner = u.id
                LIMIT %s, %s
              """.format(filehub=self.table, user='user')
        start_page = (params['now_page'] - 1) * params['page_number']
        arg = [
                FULL_DATE_FORMAT,
                FULL_DATE_FORMAT,
                params['file_id'],
                UPLOAD_STATUS['uploaded'],
                start_page,
                params['page_number']
        ]
        cur = yield self.db.execute(sql, arg)
        data = cur.fetchall()
        return data

    @coroutine
    def total_pages(self, pid):
        sql = "SELECT count(*) as number FROM {table} WHERE pid = %s AND upload_status = %s".format(table=self.table)
        cur = yield self.db.execute(sql, [pid, UPLOAD_STATUS['uploaded']])
        data = cur.fetchone()
        return data['number']
