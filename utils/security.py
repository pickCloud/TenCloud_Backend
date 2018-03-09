__author__ = 'Jon'

import re
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from setting import settings


def password_strength(password):
    ''' 数字，小写，大写，特殊字符
        长度 < 8  很弱
        长度 >= 8 包含一种弱，包含两种一般，包含三种强，包含4种很强
    '''
    strength = ('很弱', '弱', '一般', '强', '很强')

    if len(password) < 8:
        return strength[0]
    else:
        digit_match = re.search(r'[0-9]', password)
        lower_match = re.search(r'[a-z]', password)
        upper_match = re.search(r'[A-Z]', password)
        symbol_match = re.search(r'[\"\'~!@#$%^&\\*\(\)_=\+\|,./\?:;\[\]\{\}<>]', password)

        matches = [digit_match, lower_match, upper_match, symbol_match]

        return strength[len(matches) - matches.count(None)]

class Aes():
    key = settings['aes_key'].encode()
    length = len(key)
    mode = AES.MODE_CBC

    @classmethod
    def encrypt(cls, text):
        '''
        :param text: 如果text不是16的倍数【加密文本text必须为16的倍数！】，那就补足为16的倍数
        :return: 因为AES加密时候得到的字符串不一定是ascii字符集的，输出到终端或者保存时候可能存在问题
                 所以这里统一把加密后的字符串转化为16进制字符串

        Usage::
            >>> Aes.encrypt(text)
        '''
        cryptor = AES.new(cls.key, cls.mode, cls.key)
        text = text.encode("utf-8")
        count = len(text)
        add = cls.length - (count % cls.length)
        text = text + (b'\0' * add)
        ciphertext = cryptor.encrypt(text)

        return b2a_hex(ciphertext).decode("ASCII")

    @classmethod
    def decrypt(cls, text):
        '''解密后，去掉补足的空格用strip() 去掉

        Usage::
            >>> Aes.decrypt(text)
        '''
        cryptor = AES.new(cls.key, cls.mode, cls.key)
        plain_text = cryptor.decrypt(a2b_hex(text))

        return plain_text.rstrip(b'\0').decode("utf-8")