
from service.base import BaseService

class ServiceService(BaseService):
    table = 'service'
    fields = """
                id, name, app_id, type, state, source, yaml, log, verbose, lord, form
            """