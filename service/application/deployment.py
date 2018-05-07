
from service.base import BaseService
from utils.ssh import SSH
from constant import K8S_DEPLOY_CMD


class DeploymentService(BaseService):
    table = 'deployment'
    fields = """
                id, name, status, app_id, type, yaml,
                server_id, verbose, lord, form
            """

    def k8s_deploy(self, params, out_func=None):
        cmd = K8S_DEPLOY_CMD + params['filename']
        ssh = SSH(hostname=params['public_ip'], port=22, username=params['username'], passwd=params['passwd'])
        out, err = ssh.exec_rt(cmd, out_func)
        return out, err

    def add_deployment(self, params):
        sql = """
                INSERT INTO deployment (name, status, app_id, type, yaml, server_id, verbose, form, lord) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) 
                ON DUPLICATE key UPDATE status=%s, update_time=NOW(), yaml=%s, server_id=%s, verbose=%s
              """
        arg = [params['name'], params['status'],  params['app_id'], params['type'], params['yaml'], params['server_id'],
               params['verbose'], params['form'], params['lord'], params['status'], params['yaml'], params['server_id'],
               params['verbose']]
        self.sync_db_execute(sql, arg)