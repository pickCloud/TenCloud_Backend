from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.decorator import is_login
from utils.context import catch
from constant import SUCCESS, FAILURE, OPERATION_OBJECT_STYPE, OPERATE_STATUS, LABEL_TYPE, \
                     RIGHT, SERVICE, FORM_COMPANY, FORM_PERSON, MSG_PAGE_NUM, APPLICATION_STATE, DEPLOYMENT_STATUS, \
                     SERVICE_STATUS

class LabelListHandler(BaseHandler):
    @is_login
    @coroutine
    def get(self):
        """
        @api {get} /api/label/list 标签列表
        @apiName LabelListHandler
        @apiGroup Label

        @apiUse cidHeader

        @apiParam {Number} type 标签类型(1.应用,2.镜像)

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": 1,
                        "name": "Label_One"
                    },
                    ...
                ]
            }
        """
        with catch(self):
            param = self.get_lord()
            param['type'] = self.params.get('type')
            result = yield self.label_service.select(conds=param, fields='id,name', ct=False, ut=False)

            self.success(result)


class LabelAddHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/label/new 创建标签
        @apiName LabelAddHandler
        @apiGroup Label

        @apiUse cidHeader

        @apiParam {String} name 标签名称
        @apiParam {Number} type 标签类型(1.应用,2.镜像)

        @apiUse Success
        """
        with catch(self):
            self.guarantee('name')

            param = self.get_lord()
            param['type'] = LABEL_TYPE['application']
            param['name'] = self.params.get('name')

            label = yield self.label_service.select(conds=param)
            if label:
                self.log.info('The label exists, name: %s, type: %d' % (param['name'], param['type']))
                self.error('添加的标签【%s】已经存在' % param['name'])
            else:
                yield self.label_service.add(param)
                self.log.info('Succeed in add the label, name: %s, type: %d' % (param['name'], param['type']))
                self.success()


class LabelDelHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/label/del 删除标签
        @apiName LabelDelHandler
        @apiGroup Label

        @apiUse cidHeader

        @apiParam {Number} id 标签ID

        @apiUse Success
        """
        with catch(self):
            self.guarantee('id')

            yield self.label_service.delete(conds={'id': self.params.get('id')})
            self.log.info('Succeed in del the label, ID: %d' % (self.params.get('id')))

            self.success()