__author__ = 'Jon'

from service.base import BaseService


class ProjectService(BaseService):
    table  = 'project'
    fields = 'id, name, description, repository'