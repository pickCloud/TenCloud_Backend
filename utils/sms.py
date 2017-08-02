__author__ = 'Jon'

from twilio.rest import Client
from setting import settings

class SMS:
    account_sid = settings['sms_account_sid']
    auth_token  = settings['sms_auth_token']

    @classmethod
    def send(cls, to, from_=settings['sms_from_number'], body='', prefix='+86'):
        """
        :param to: 接收的手机号
        :param from_: 发送的手机号
        :param body: 内容
        :return:

        Usage::
            >>> SMS.send(to='', body='')
        """
        try:
            client = Client(cls.account_sid, cls.auth_token)
            result = client.messages.create(to=prefix+to,
                                            from_=from_,
                                            body=body)

            return {'sid': result.sid}
        except Exception as e:
            return {'err': str(e)}