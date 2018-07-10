
from service.base import BaseService
from utils.ssh import SSH
from constant import K8S_APPLY_CMD


class DeploymentService(BaseService):
    table = 'deployment'
    fields = """
                id, name, status, app_id, type, yaml,
                server_id, verbose, log, lord, form
            """

    def add_deployment(self, params):
        sql = """
                INSERT INTO deployment (name, status, app_id, type, yaml, server_id, log, form, lord) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
                ON DUPLICATE key UPDATE status=%s, update_time=NOW(), yaml=%s, server_id=%s, log=%s
              """
        arg = [params['name'], params['status'],  params['app_id'], params['type'], params['yaml'], params['server_id'],
               params['log'], params['form'], params['lord'], params['status'], params['yaml'], params['server_id'],
               params['log']]
        index = self.sync_db_execute(sql, arg)
        return {'id': index}


class ReplicaSetService(BaseService):
    table = 'replicaset'
    fields = "id, name, deployment_id, verbose"

class PodService(BaseService):
    table = 'pod'
    fields = "id, name, deployment_id, verbose"
