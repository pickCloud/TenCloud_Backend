
from service.base import BaseService

class ImageService(BaseService):
    table = '_image'
    fields = """
                id, name, version, type, url, description, labels, 
                state, app_id, log, lord, form
            """
