from service.base import BaseService


class PermissionTemplateService(BaseService):
    table = 'permission_template'
    fields = """
            id, name, cid, permissions, access_servers, access_projects,
            access_projects, access_filehub
            """
