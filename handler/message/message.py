import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login
from utils.context import catch


class MessageHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, status):
        """
        @api {get} /api/messages/?(\d*)?page=\d&mode=\d 获取员工消息列表, mode值看下面的response
        @apiName MessageGetHandler
        @apiGroup Message

        @apiDescription /0未读,  /1已读, /全部。没有page,返回所有

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"id": 1, "content": "十全十美",
                    "url": "http",
                    "mode": "1加入企业，2企业改变信息",
                    "sub_mode": "0马上审核, 1重新提交, 2进入企业, 3马上查看"
                    "status": "0未读，1已读",
                    "tip": "cid:code"}
                ]
            }
        """
        with catch(self):
            params = {'owner': self.current_user['id']}

            if self.get_argument('page', None):
                params['page'] = int(self.get_argument('page'))

            if self.get_argument('mode', None):
                params['mode'] = int(self.get_argument('mode'))

            if status:
                params['status'] = int(status)

            data = yield self.message_service.fetch(params)

            self.success(data)