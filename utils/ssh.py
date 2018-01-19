__author__ = 'Jon'

import select
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
            self._client.connect(hostname=hostname, port=port, username=username, password=passwd,
                                 timeout=SSH_CONNECT_TIMEOUT)
        except Exception as e:
            self.close()
            raise e

    def _log(self, data, msg):
        LOG.info('SSH {msg}:{rs}{data}'.format(msg=msg, rs='\n', data=''.join(data)))

    def exec(self, cmd):
        LOG.info('SSH CMD: %s' % cmd)

        stdin, stdout, stderr = self._client.exec_command(cmd, get_pty=True)

        out, err = stdout.readlines(), stderr.readlines()

        if err:
            self._log(err, 'ERR')
        else:
            self._log(out, 'OUT')

        return out, err

    def exec_rt(self, cmd, out_func=None):
        ''' 实时显示远端信息
            Usage::
                >>> out, err = ssh.exec_rt('top -b -n 5', self.write_message) # tornado websocket
        '''
        LOG.info('SSH CMD: %s' % cmd)

        stdin, stdout, stderr = self._client.exec_command(cmd, get_pty=True)
        channel = stdout.channel
        pending = err_pending = None

        if not out_func: out_func = print

        out, err = [], []

        while not channel.closed or channel.recv_ready() or channel.recv_stderr_ready():
            readq, _, _ = select.select([channel], [], [], 1)
            for c in readq:
                if c.recv_ready():
                    chunk = c.recv(len(c.in_buffer))
                    if pending is not None:
                        chunk = pending + chunk
                    lines = chunk.splitlines()
                    if lines and lines[-1] and lines[-1][-1] == chunk[-1]:
                        pending = lines.pop()
                    else:
                        pending = None

                    for line in lines:
                        out_func(line)
                        line = line.decode('utf-8')
                        out.append(line)

                if c.recv_stderr_ready():
                    chunk = c.recv_stderr(len(c.in_stderr_buffer))
                    if err_pending is not None:
                        chunk = err_pending + chunk
                    lines = chunk.splitlines()
                    if lines and lines[-1] and lines[-1][-1] == chunk[-1]:
                        err_pending = lines.pop()
                    else:
                        err_pending = None

                    for line in lines:
                        out_func(line)
                        line = line.decode('utf-8')
                        err.append(line)

        if err == ['[', ']']: err = []

        return out, err

    def close(self):
        self._client.close()