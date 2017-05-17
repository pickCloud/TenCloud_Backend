__author__ = 'Jon'

'''
一些平常的工具
'''

def get_in_format(contens):
    '''
    :param contens: e.g. [1, 2, 3]
    :return: e.g. '%s, %s, %s'
    '''
    return ','.join(['%s'] * len(contens))