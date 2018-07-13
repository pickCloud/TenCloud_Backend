
from tornado.gen import coroutine
from tornado.ioloop import IOLoop
from handler.base import BaseHandler, WebSocketBaseHandler
from utils.decorator import is_login, require
from utils.context import catch
from utils.general import validate_image_name
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

        @apiParam {Number} [id] 镜像ID
        @apiParam {Number} [app_id] 应用ID
        @apiParam {Number} [state] 镜像状态(0.初创建 1.正常 2.异常)
        @apiParam {Number} [page] 页数
        @apiParam {Number} [page_num] 每页显示项数
        @apiParam {Number} [label] 镜像标签ID

        @apiDescription 样例: /api/image?id=\d&app_id=\d&type=\d&page=\d&page_num=\d&label=\d

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": [
                    {
                        "id": int,              //镜像ID
                        "app_id": int,          //应用ID
                        "name": str,
                        "description": str,
                        "version": str,
                        "type": int,            //镜像类型(1.内部应用, 2.外部镜像)
                        "state": int,           //镜像构建结果(0.构建中 1.成功 2.失败)
                        "url": str,             //镜像路径
                        "labels": str,          //镜像标签编号
                        "label_name": str,      //镜像标签名称
                        "logo_url": str,        //镜像图标地址
                        "commit": str,          //镜像commit标签
                        "dockerfile": str,      //Dockerfile
                        "repos_name": str,      //代码仓库名称
                        "repos_url": str,       //仓库地址
                        "log": str,             //日志
                        "form": int,
                        "lord": int,
                        "create_time": str,
                        "update_time": str
                    },
                    ...
                ]
            }
        """
        with catch(self):
            param = self.get_lord()
            if self.params.get('app_id'):
                param['app_id'] = self.params.get('app_id')
            if self.params.get('id'):
                param['id'] = self.params.get('id')

            page = self.params.get('page', 1)
            page_num = self.params.get('page_num', MSG_PAGE_NUM)
            label = int(self.params.get('label', 0))

            data = yield self.image_service.fetch_with_label(param, label)

            self.success(data[page_num * (page - 1):page_num * page])


class ImageNewHandler(BaseHandler):
    @is_login
    @coroutine
    def post(self):
        """
        @api {post} /api/image/new 创建新镜像
        @apiName ImageNewHandler
        @apiGroup Image

        @apiUse cidHeader

        @apiParam {String} name 镜像名称
        @apiParam {String} version 镜像版本
        @apiParam {Number} type 镜像类型(1.内部应用, 2.外部镜像)
        @apiParam {String} description 描述
        @apiParam {String} url 镜像URL
        @apiParam {String} logo_url LOGO地址
        @apiParam {String} repos_name 代码仓库名称
        @apiParam {String} repos_url 代码仓库github地址
        @apiParam {String} dockerfile dockerfile
        @apiParam {Number} app_id 所属应用ID
        @apiParam {[]Number} labels 标签ID(传递时注意保证ID是从小到大的顺序)

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 200 OK
            {
                "status": 0,
                "msg": "success",
                "data": {
                    "id": int,
                    "update_time": time
                }
            }
        """
        with catch(self):
            self.guarantee('name', 'version', 'app_id')
            self.log.info('Create new image, name: %s, version: %s, app_id: %s'
                          % (self.params.get('name'), self.params.get('version'), self.params.get('app_id')))

            validate_image_name('name')
            param = self.params
            param.pop('token', None)
            param.pop('cid', None)
            param.update(self.get_lord())
            param['labels'] = ','.join(str(i) for i in param.pop('labels', []))
            param['logo_url'] = settings['qiniu_header_bucket_url'] + param['logo_url'] if self.params.get('logo_url', None) else ''

            new_image = yield self.image_service.add(param)

            self.log.info('Succeeded to create new image, name: %s, version: %s, app_id: %s'
                          % (self.params.get('name'), self.params.get('version'), self.params.get('app_id')))
            self.success(new_image)