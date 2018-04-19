
from service.base import BaseService

class ImageService(BaseService):
    table = '_image'
    fields = """
                id, name, version, type, url, description, labels, logo_url, commit,
                state, dockerfile, repos_name, repos_url, app_id, log, lord, form
            """
