import sys
import json
import time
import socket
import psutil
import requests
import subprocess

def get_ip_address():
    cmd = 'curl ifconfig.me'
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    stdout, stderr = p.communicate()

    return stdout.strip().decode('utf8')

def get_cpu():
    r = psutil.cpu_percent(interval=1)

    return {'percent': r}

def get_mem():
    r = psutil.virtual_memory()

    return {'total': r.total, 'percent': r.percent, 'available': r.available, 'free': r.free}

def get_disk():
    r = psutil.disk_usage('/')

    return {'total': r.total, 'percent': r.percent, 'free': r.free}


if __name__ == '__main__':
    while True:
        data = {
            'ip': get_ip_address(),
            'cpu': get_cpu(),
            'mem': get_mem(),
            'disk': get_disk(),
            'token': sys.argv[1]
        }

        url = 'http://47.94.18.22'
        kw = dict(
            data=json.dumps(data),
            headers={'Content-type': 'application/json'},
            timeout=5
        )

        requests.post(url + '/remote/server/report', **kw)
        time.sleep(5)
