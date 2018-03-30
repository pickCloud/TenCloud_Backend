
from service.base import BaseService

class ServiceService(BaseService):
    table = 'service'
    fields = """
                id, name, deploy_id, type, status, lord, form
            """