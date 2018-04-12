import time
import random
from utils.datetool import seconds_to_human

cpu_percent = lambda : random.randint(0, 100)
disk_free = lambda : random.randint(0, 40000000000)
disk_total = lambda : random.randint(42139451392, 48139451392)
disk_percent = lambda total, free: round((total-free)/total, 4)*100
mem_free = lambda : random.randint(0, 4046408000)
mem_total = mt = 4046408000  # 4G
mem_available = lambda total, free: total - free
mem_percent = disk_percent
net_input = lambda : random.randint(0, 1000)
net_output = lambda : random.randint(0, 1000)
load = lambda : round(random.random(), 2)

def is_faker(s):
    ''' 数据库instance_id以f开头的都是模拟数据 '''
    return s.startswith('f')


def fake_report_info():
    df = disk_free()
    dt = disk_total()
    dp = disk_percent(dt, df)

    mf = mem_free()
    mp = mem_percent(mt, mf)
    ma = mem_available(mt, mf)

    report_info = {
        'cpu': {'percent': cpu_percent()},
        'disk': {'free': df,
                 'percent': dp,
                 'total': dt,
                 'utilize': 0},
        'docker': None,
        'memory': {'available': ma,
                   'free': mf,
                   'percent': mp,
                   'total': mt},
        'net': {'input': net_input(), 'output': net_output()},
        'system_load': {'date': seconds_to_human(),
                        'fifth_minute_load': load(),
                        'five_minute_load': load(),
                        'login_users': 1,
                        'one_minute_load': load(),
                        'run_time': '{}小时{}分钟{}秒'.format(random.randint(0, 1000), random.randint(1, 59), random.randint(1, 59))},
        'time': time.time(),
        'token': ''
    }


    return report_info

def fake_performance(params):
    start, end = int(params['start_time']), int(params['end_time'])
    times = list(range(start, end, int((end-start)/7)))

    cpu, disk, memory, net = [], [], [], []
    for t in times:
        cpu.append({'percent': cpu_percent(), 'created_time': t})

        df = disk_free()
        dt = disk_total()
        dp = disk_percent(dt, df)
        disk.append({'percent': dp, 'created_time': t, 'free': df, 'total': dt, 'utilize': 0})

        mf = mem_free()
        mp = mem_percent(mt, mf)
        ma = mem_available(mt, mf)
        memory.append({'percent': mp, 'created_time': t, 'free': mf, 'available': ma, 'total': mt})

        net.append({'created_time': t, 'input': net_input(), 'output': net_output()})


    performance = {
        'cpu': cpu,
        'disk': disk,
        'memory':  memory,
        'net': net
    }

    return  performance


if __name__ == '__main__':
    from pprint import pprint

    pprint(is_faker('f--'))
    pprint(is_faker('i--'))

    pprint(fake_report_info())

    pprint(fake_performance({'start_time': '1523504015', 'end_time': '1523507615'}))