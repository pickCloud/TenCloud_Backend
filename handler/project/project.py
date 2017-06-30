__author__ = 'Jon'

import traceback

from tornado.gen import coroutine
from handler.base import BaseHandler
from utils.general import get_in_formats
from setting import settings


class ProjectHandler(BaseHandler):
    @coroutine
    def get(self):
        ''' 获取列表
        '''
        try:
            result = yield self.project_service.select(ct=False)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectNewHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 新建
            参数:
                {"name":        名称 str,
                 "description": 描述 str,
                 "repos_name":  仓库名称 str,
                 "repos_url":   仓库url str}
        '''
        try:
            result = yield self.project_service.add(params=self.params)

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectDelHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 删除
            参数: {"id": list}
        '''
        try:
            ids = self.params['id']

            yield self.project_service.delete(conds=[get_in_formats('id', ids)], params=ids)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectDetailHandler(BaseHandler):
    @coroutine
    def get(self, id):
        ''' 详情
        '''
        try:
            result = yield self.project_service.select(conds=['id=%s'], params=[id])

            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectUpdateHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 更新
        '''
        try:
            sets = ['name=%s', 'description=%s', 'repos_name=%s', 'repos_url=%s']
            conds = ['id=%s']
            params = [self.params['name'], self.params['description'], self.params['repos_name'],
                      self.params['repos_url'], self.params['id']]

            yield self.project_service.update(sets=sets, conds=conds, params=params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectDeploymentHandler(BaseHandler):
    @coroutine
    def post(self):
        """ 部署镜像
        """
        try:
            login_info = yield self.server_service.fetch_ssh_login_info(self.params)
            self.params.update(login_info)
            yield self.project_service.deployment(self.params)
            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectImageCreationHandler(BaseHandler):
    @coroutine
    def post(self):
        ''' 构建仓库镜像
        '''
        try:

            login_info = yield self.server_service.fetch_ssh_login_info(
                {'public_ip': settings['ip_for_image_creation']})
            self.params.update(login_info)

            yield self.project_service.create_image(self.params)

            self.success()
        except:
            self.error()
            self.log.error(traceback.format_exc())


class ProjectImageFindHandler(BaseHandler):
    @coroutine
    def get(self):
        """
        获取某一项目的所有镜像信息
        """
        try:
            prj_name = {"prj_name": self.get_argument('prj_name')}
            self.params.update(prj_name)
            login_info = yield self.server_service.fetch_ssh_login_info(
                {'public_ip': settings['ip_for_image_creation']})

            self.params.update(login_info)
            datas, err = yield self.project_service.find_image(self.params)
            result = []
            for data in datas[:2]:
                e = data.split(',')
                tmp = {'tag': e[0], 'created': e[1]}
                result.append(tmp)
            if err:
                self.error(err)
                return
            self.success(result)
        except:
            self.error()
            self.log.error(traceback.format_exc())

