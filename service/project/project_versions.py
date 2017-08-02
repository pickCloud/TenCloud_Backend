from service.base import BaseService


class ProjectVersionService(BaseService):
    table  = 'project_versions'
    fields = 'id, name, version, log'
