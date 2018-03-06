import os
import machine
import uipc
import drv8835
from config import robot as config


def autoreply(f):
    def _f(self, port, msg):
        try:
            f(self, port, msg)
            port.success()
        except Exception as e:
            print(msg, '... failed:', e)
            port.failure(str(e))
    return _f

class RobotService(uipc.ServiceBase):

    def __init__(self):
        from display import text_board
        self._logger = text_board.putline
        self._drv = None

    @autoreply
    def enable(self, port, msg):
        self._drv = drv8835.DRV8835(config.drv8835_mode,
                                    config.A_in1, config.A_in2,
                                    config.B_in1, config.B_in2)
        self._logger('drv8835 is enabled.')

    @autoreply
    def duty(self, a_duty, b_duty):
        self._drv.duty_a(a_duty)
        self._drv.duty_b(b_duty)

def register(port):
    uipc.manager.register_server(port, RobotService())
