import time
import random
from utils.datetool import seconds_to_human

def is_faker(s):
    ''' 数据库instance_id以f开头的都是模拟数据 '''
    return s.startswith('f')

def fake_performance():
    cpu_percent = random.randint(0, 100)
    disk_free = random.randint(0, 40000000000)
    disk_total = random.randint(42139451392, 48139451392)
    mem_free = random.randint(0, 4046408000)
    mem_total = 4046408000 # 4G
    net_input = random.randint(0, 1000)
    net_output = random.randint(0, 1000)
    load = round(random.random(), 2)


    performance = {
        'cpu': {'percent': cpu_percent},
        'disk': {'free': disk_free,
                 'percent': round((disk_total-disk_free)/disk_total, 4)*100,
                 'total': disk_total,
                 'utilize': 0},
        'docker': None,
        'memory': {'available': mem_total - mem_free,
                   'free': mem_free,
                   'percent': round((mem_total-mem_free)/mem_total, 4)*100,
                   'total': mem_total},
        'net': {'input': net_input, 'output': net_output},
        'system_load': {'date': seconds_to_human(),
                        'fifth_minute_load': load,
                        'five_minute_load': load,
                        'login_users': 1,
                        'one_minute_load': load,
                        'run_time': '{}小时{}分钟{}秒'.format(random.randint(0, 1000), random.randint(1, 59), random.randint(1, 59))},
        'time': time.time(),
        'token': ''
    }


    return performance


if __name__ == '__main__':
    from pprint import pprint
    pprint(fake_performance())

    pprint(is_faker('f--'))
    pprint(is_faker('i--'))