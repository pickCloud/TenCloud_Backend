__author__ = 'Jon'

from service.base import BaseService


class ClusterService(BaseService):
    table  = 'cluster'
    fields = 'id, name, description, status'