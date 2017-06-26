__author__ = 'Jon'

import paramiko

from utils.log import LOG
from constant import SSH_CONNECT_TIMEOUT


class SSHError(Exception):
    pass

class SSH:
    '''
    Usage::
            >>> ssh = SSH()
            >>> ssh.exec('cmd')
            >>> ssh.close()
    '''
    def __init__(self, hostname=None, port=22, username=None, passwd=None, logpath='logs/sysdeploy.log'):
        paramiko.util.log_to_file(logpath)

        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            self._client.connect(hostname=hostname, port=port, username=username, password=passwd, timeout=SSH_CONNECT_TIMEOUT)
        except Exception as e:
            self.close()
            raise e

    def exec(self, cmd):
        LOG.info('SSH command: %s' % cmd)

        stdin, stdout, stderr = self._client.exec_command(cmd)

        out = stdout.read()
        LOG.debug("SSH received stdout: %s" % out)

        ret = stdout.channel.recv_exit_status()
        LOG.debug("SSH exit status: %s" % ret)

        err = stderr.read()
        LOG.debug("SSH received stderr:\n%s" % err)

        if ret:
            raise Exception("Error executing %s" % cmd)

        return (out, err)

    def close(self):
        self._client.close()