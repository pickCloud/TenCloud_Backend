from service.base import BaseService
from tornado.concurrent import run_on_executor
from utils.sms import SMS
from constant import SMS_TIP


class UserService(BaseService):
    table = 'user'
    fields = 'id, mobile, email, name, image_url'

    @run_on_executor
    def send_sms(self, mobile, code):

        result = SMS.send(to=mobile, body=SMS_TIP.format(code=code))

        return result