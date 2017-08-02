__author__ = 'Jon'

'''
一些装饰器
'''
import functools

def is_login(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            self.error('require login', code=403)
            return

        return method(self, *args, **kwargs)

    return wrapper