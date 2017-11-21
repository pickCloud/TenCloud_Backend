import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login
from constant import MSG_STATUS


class MessageHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, status):
        """
        @api {get} /api/messages/?(\d*)?page=\d 获取员工消息列表
        @apiName MessageGetHandler
        @apiGroup Message

        @apiDescription /0未读,  /1已读, /全部。page默认为1

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"id": 1, "content": "十全十美",
                    "url": "http",
                    "mode": "1加入企业，2企业改变信息",
                    "status": "0未读，1已读",
                    "tip": "马上审核/重新提交/..."}
                ]
            }
        """
        try:
            params = {'owner': self.current_user['id'], 'page': self.get_argument('page', 1)}

            if status: params['status'] = status

            data = yield self.message_service.fetch(params)

            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())