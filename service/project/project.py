__author__ = 'Jon'

from service.base import BaseService


class ProjectService(BaseService):
    table  = 'project'
    fields = 'id, name, description, repos_name, repos_url'