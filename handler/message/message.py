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

            if self.params.get('page'):
                params['page'] = int(self.params['page'])

            if self.params.get('mode'):
                params['mode'] = int(self.params['mode'])

            if status:
                params['status'] = int(status)

            data = yield self.message_service.fetch(params)

            self.success(data)


# 获取当前用户的消息数量
class MessageCountHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/messages/count 获取员工消息数目
        @apiName MessageCountHandler
        @apiGroup Message

        @apiParam {Number} status 消息状态
        @apiDescription status代表需要查询的消息状态 /0未读,  /1已读, 不传递代表查询所有类型的消息

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "num" : 0
                    }
                ]
            }
        """
        with catch(self):
            # 封装参数，用户id直接获取，status通过api参数传入
            params = {'owner': self.current_user['id']}
            if self.params.get('status'):
                params['status'] = self.params.get('status')

            # 调用service层数据库查询接口，取出指定参数对应的数据
            message_data = yield self.message_service.select(params)

            data = {
                'num': len(message_data)
            }
            self.success(data)


class MessageSearchHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        '''
        @api {get} /api/messages/search 查找消息
        @apiName MessageSearchHandler
        @apiGroup Message

        @apiDescription 通过关键字以及消息类型，消息状态进行查找消息

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {"id": 1,
                    "owner": 1,
                    "content": "十全十美",
                    "mode": "1加入企业，2企业改变信息，3离开企业",
                    "sub_mode": "0马上审核, 1重新提交, 2进入企业, 3马上查看",
                    "tip": "cid:code",
                    "status": "0未读，1已读",}
                ]
            }
        '''
        with catch(self):
            # 封装参数，用户id直接获取，mode,status和keywords通过api参数传入
            params = {'owner': self.current_user['id']}
            if self.params.get('status') is not None:
                params['status'] = self.params.get('status')
            if self.params.get('mode'):
                params['mode'] = self.params.get('mode')

            # 模糊匹配关键字，使用%%转义
            extra = ' AND content LIKE "%%{keywords}%%"'.format(keywords=self.params.get('keywords') or '')
            extra += ' ORDER BY update_time DESC '
            message_data = yield self.message_service.select(conds=params, extra=extra)

            self.success(message_data)