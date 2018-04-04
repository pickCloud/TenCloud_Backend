
import os
import re
from tornado.gen import coroutine
from tornado.concurrent import run_on_executor
from service.base import BaseService
from utils.ssh import SSH
from utils.security import Aes
from constant import CREATE_IMAGE_CMD, IMAGE_INFO_CMD, DEPLOY_CMD, \
                     REPOS_DOMAIN, LIST_CONTAINERS_CMD, LOAD_IMAGE_FILE,\
                     LOAD_IMAGE, CLOUD_DOWNLOAD_IMAGE, YE_PORTMAP
from setting import settings

class ApplicationService(BaseService):
    table = 'application'
    fields = """
                id, name, description, status, repos_name, 
                repos_ssh_url, repos_https_url, logo_url, 
                image_id, lord, form
            """
