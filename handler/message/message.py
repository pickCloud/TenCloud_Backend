import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login
from constant import MSG_STATUS


class MessageHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self, mode):
        """
        @api {get} /api/messages/?(\d*) 获取员工消息列表
        @apiName MessageGetHandler
        @apiGroup Message

        @apiDescription /1加入企业,  /2企业变更, /全部

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"id": 1, "content": "十全十美", "url": "http", "mode": "1加入企业，2企业改变信息", "status": "0未读，1已读"}
                ]
            }
        """
        try:
            params = {'owner': self.current_user['id']}

            if mode: params['mode'] = mode

            data = yield self.message_service.fetch(params)

            self.success(data)
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())

    @is_login
    @coroutine
    def post(self, id):
        """
        @api {get} /api/messages/(\d+) 标记消息id已读
        @apiName MessagePostHandler
        @apiGroup Message

        @apiUse Success
        """
        try:
            yield self.message_service.check_owner({'owner': self.current_user['id'], 'id': id})

            yield self.message_service.update(sets=['status=%s'], conds=['id=%s'], params=[MSG_STATUS['read'], id])

            self.success()
        except Exception as e:
            self.error(str(e))
            self.log.error(traceback.format_exc())
