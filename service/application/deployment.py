
from service.base import BaseService


class DeploymentService(BaseService):
    table = 'deployment'
    fields = """
                id, name, status, app_id, type, config_id,
                server_id, verbose, lord, form
            """