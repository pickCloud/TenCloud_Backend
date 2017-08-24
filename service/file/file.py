
from qiniu import Auth
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor
from service.base import BaseService
from constant import QINIU_POLICY
from setting import settings


class FileService(BaseService):
    table = 'filehub'
    fields = 'id, filename, size, qiniu_id, owner, mime, hash, type, pid'

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
        sql = "SELECT size, qiniu_id, mime FROM {table} WHERE hash=%s".format(table=self.table)
        arg = [hash]
        cur = yield self.db.execute(sql, arg)
        return cur.fetchone()

    @coroutine
    def seg_page(self, params):
        sql = """SELECT id, filename, size, qiniu_id, owner, mime, hash, type, pid, create_time, update_time 
                FROM %s LIMIT %s,%s
              """
        start_page = (params['now_page'] - 1) * params['page_number'] + 1
        arg = [self.table, start_page, start_page+params['page_number']]
        cur = yield self.db.execute(sql, arg)
        data = cur.fetchall()
        return data
