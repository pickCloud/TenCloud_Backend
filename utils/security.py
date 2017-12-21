__author__ = 'Jon'

from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
from setting import settings
import passwordmeter


def password_strength(password):
    ratings = (
        '弱爆了',
        '极其弱',
        '非常弱',
        '弱',
        '中等',
        '一般',
        '非常强',
    )
    strength, _ = passwordmeter.test(password)
    result = min(len(ratings) - 1, int(strength * len(ratings)))
    return result


class Aes():
    key = settings['aes_key']
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