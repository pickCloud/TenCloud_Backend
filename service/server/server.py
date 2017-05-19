__author__ = 'Jon'

from tornado.gen import coroutine
from service.base import BaseService
from constant import CLUSTER_DATE_FORMAT


class ServerService(BaseService):
    table  = 'server'
    fields = 'id, name, address, ip, machine_status, business_status'