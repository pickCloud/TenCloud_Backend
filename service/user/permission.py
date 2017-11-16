from service.base import BaseService


class PermissionService(BaseService):
    table = 'permission'
    fields = 'id, name'


