__author__ = 'Jon'

'''
一些自定义的Error
'''
from constant import FAILURE_STATUS

class AppError(Exception):
    """ Usage:
            >>> from constant import ERR_TIP
            >>> raise AppError(ERR_TIP['access_denied']['msg'], ERR_TIP['access_denied']['sts'])
    """
    def __init__(self, msg='', status=FAILURE_STATUS):
        super().__init__(msg, status)
        self.msg = msg
        self.status = status

    def __str__(self):
        return self.msg