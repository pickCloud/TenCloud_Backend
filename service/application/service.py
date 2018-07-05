
from service.base import BaseService

class ServiceService(BaseService):
    table = 'service'
    fields = """
                id, name, app_id, type, state, source, yaml, log, verbose, lord, form
            """


class EndpointService(BaseService):
    table = 'endpoint'
    fields = """
                id, name, service_id, verbose
            """


class IngressService(BaseService):
    table = 'ingress'
    fields = "id, name, app_id, verbose"
