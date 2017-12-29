__author__ = 'Jon'

'''
一些装饰器
'''
import functools
from tornado.gen import coroutine

def is_login(method):
    ''' 登录认证
    Usage:
        @is_login
        def get(self):
            self.success()
    '''
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            self.error('require login', code=403)
            return

        return method(self, *args, **kwargs)

    return wrapper

def find(handler, args, target='cid'):
    ''' 存在于json,或是url参数,或是url第一个参数
    :param handler: handler的实例
    :param args: urlpath的变量
    :param target: 目标参数
    :return: int/list/tuple
    '''
    v = handler.params.get(target) or (args and args[0])

    if isinstance(v, (list, tuple)):
        return v
    else:
        return int(v)

def auth(role):
    ''' 员工认证，管理员认证, 没有cid代表个人
    :param role: enum('staff', 'admin')

    Usage:
        @auth('staff')
        def get(self, cid):
            self.success()
    '''
    def is_role(method):
        @is_login
        @coroutine
        def wrapper(self, *args, **kwargs):

            try:
                cid = find(self, args)

                if cid:
                    yield getattr(self.company_employee_service, 'check_{role}'.format(role=role))(cid, self.current_user['id'])
            except Exception as e:
                self.error(str(e))
                return

            yield method(self, *args, **kwargs)

        return wrapper
    return is_role

def require(*pids, service=None):
    ''' 员工需要有pids的权限, 及是否进行数据权限操作
    :param pids: 对应permission表id, 功能权限
    :params service:   数据权限对应的类
    Usage:
        from constant import SERVICE
        @require(1, 2, s=SERVICE['s'])
        def get(self):
            self.success()
    '''
    def allow(method):
        @auth('staff')
        @coroutine
        def wrapper(self, *args, **kwargs):

            try:
                cid = find(self, args)

                if cid:
                    try:
                        yield self.company_employee_service.check_admin(cid, self.current_user['id'])  # 管理员不需要检查
                    except ValueError:
                        yield self.user_permission_service.check_right({'cid': cid, 'uid': self.current_user['id'], 'ids': pids})

                        if service:
                            ids = find(self, args, target='id')
                            yield getattr(self, service).check_right({'cid': cid, 'uid': self.current_user['id'], 'ids': ids})

            except Exception as e:
                self.error(str(e))
                return

            yield method(self, *args, **kwargs)

        return wrapper
    return allow
