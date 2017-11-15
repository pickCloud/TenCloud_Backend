from service.base import BaseService
from tornado.gen import coroutine

class PermissionService(BaseService):
    table = 'permission'
    fields = 'id, name'

    @coroutine
    def get_permission_detail(self, id):
        sql = """
                SELECT 
             """
        pass
