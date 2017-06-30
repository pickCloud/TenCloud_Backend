__author__ = 'Jon'

import paramiko

from utils.log import LOG
from constant import SSH_CONNECT_TIMEOUT


class SSHError(Exception):
    pass

class SSH:
    '''
    Usage::
            >>> ssh = SSH(hostname=hostname, username=username, passwd=passwd)
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

    def _log(self, data, msg):
        LOG.info('SSH {msg}:{rs}{data}'.format(msg=msg, rs='\n', data=''.join(data)))

    def exec(self, cmd):
        LOG.info('SSH CMD: %s' % cmd)

        stdin, stdout, stderr = self._client.exec_command(cmd)

        out, err = stdout.readlines(), stderr.readlines()

        if err:
            self._log(err, 'ERR')
        else:
            self._log(out, 'OUT')

        return (out, err)

    def close(self):
        self._client.close()