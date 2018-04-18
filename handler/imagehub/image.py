
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from handler.base import BaseHandler, WebSocketBaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from utils.general import validate_application_name
from setting import settings
from constant import SUCCESS, FAILURE, OPERATION_OBJECT_STYPE, OPERATE_STATUS, LABEL_TYPE, PROJECT_OPERATE_STATUS, \
                     RIGHT, SERVICE, FORM_COMPANY, FORM_PERSON, MSG_PAGE_NUM, APPLICATION_STATE, DEPLOYMENT_STATUS, \
                     SERVICE_STATUS


class ImageDetailHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/image 镜像信息
        @apiName ImageDetailHandler
        @apiGroup Image

        @apiUse cidHeader

        @apiParam {Number} id 镜像ID
        @apiParam {Number} type 镜像状态(0.初创建 1.正常 2.异常)
        @apiParam {Number} page 页数
        @apiParam {Number} page_num 每页显示项数
        @apiParam {Number} label 镜像标签ID

        @apiDescription 样例: /api/image?id=\d&app_id=\d&type=\d&page=\d&page_num=\d&label=\d

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": int,
                        "name": str,
                        "description": str,
                        ...
                    },
                    ...
                ]
            }
        """
        with catch(self):
            param = self.get_lord()

            data = yield self.image_service.select(conds=param)

            self.success(data)