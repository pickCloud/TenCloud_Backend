__author__ = 'Jon'

'''
一些上下文管理器
'''
import traceback
from contextlib import contextmanager


@contextmanager
def catch(handler):
    ''' catch未知异常
        Usage:
            def get(self):
                with catch(self):
                    self.success()
    '''
    try:
        yield
    except Exception as e:
        if hasattr(e, 'status'):
            handler.error(str(e), status=e.status)
        else:
            handler.error(str(e))
        handler.log.error(traceback.format_exc())
        handler.finish()