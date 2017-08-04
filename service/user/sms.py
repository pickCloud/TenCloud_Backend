from service.base import BaseService
from tornado.gen import coroutine
from setting import settings
from utils.general import gen_md5

class SMSService(BaseService):

    @coroutine
    def send(self, mobile, code=''):
        param = {
            'smsUser': settings['sms_user'],
            'templateId' : settings['sms_tid'],
            'msgType': settings['sms_type'],
            'phone' : mobile,
            'vars' : '{"%code%": ' + code + '}'
        }

        param_keys = list(param.keys())
        param_keys.sort()

        param_str = ""
        for key in param_keys:
            param_str += key + '=' + str(param[key]) + '&'
        param_str = param_str[:-1]

        sign_str = settings['sms_key'] + '&' + param_str + '&' + settings['sms_key']
        sign = gen_md5(sign_str.encode('utf-8'))

        param['signature'] = sign

        result = yield self.post(settings['sms_url'], data=param)

        return result