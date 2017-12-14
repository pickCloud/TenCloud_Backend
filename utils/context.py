import traceback
from contextlib import contextmanager

@contextmanager
def catch(handler):
    ''' catch未知异常
    '''
    try:
        yield
    except Exception as e:
        handler.error(str(e))
        handler.log.error(traceback.format_exc())