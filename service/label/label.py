
from service.base import BaseService

class LabelService(BaseService):
    table = 'label'
    fields = """
                id, name, type, lord, form
            """
