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

def find_cid(handler, args):
    ''' 存在于json,或是url第一个参数,或是url参数
    :param handler: handler的实例
    :param args: urlpath的变量
    :return: cid
    '''
    cid = handler.params.get('cid') or (args and args[0])
    if not cid:
        raise ValueError('未找到cid')

    return cid

def auth(role):
    ''' 员工认证，管理员认证
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
                cid = find_cid(self, args)

                yield getattr(self.company_employee_service, 'check_{role}'.format(role=role))(cid, self.current_user['id'])
            except Exception as e:
                self.error(str(e))
                return

            yield method(self, *args, **kwargs)

        return wrapper
    return is_role

def require(*pids):
    ''' 员工需要有pids的权限
    :param pids: 对应permission表id

    Usage:
        @require(1, 2)
        def get(self):
            self.success()
    '''
    def allow(method):
        @is_login
        @coroutine
        def wrapper(self, *args, **kwargs):

            try:
                cid = find_cid(self, args)

                yield self.user_permission_service.check_permission({'cid': cid, 'uid': self.current_user['id'], 'pids': pids})
            except Exception as e:
                self.error(str(e))
                return

            yield method(self, *args, **kwargs)

        return wrapper
    return allow
