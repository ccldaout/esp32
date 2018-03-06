import os
import machine
import time

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
        self._enabled = False

    def on_accepted(self, port):
        self._loggoer('on_accepted')

    def on_disconnected(self, port):
        self._logger('on_disconnected')

    def on_exception(self, port):
        self._logger('on_exception')

    @autoreply
    def enable(self, port, msg):
        if not self._enabled:
            self._drv = drv8835.DRV8835(config.drv8835_mode,
                                        config.A_in1, config.A_in2,
                                        config.B_in1, config.B_in2)
            self._enabled = True
            self._logger('drv8835 is enabled.')
        else:
            self._logger('drv8835 is already enabled.')

    @autoreply
    def duty(self, port, msg):
        _, a_duty, b_duty = msg
        self._drv.duty_a(a_duty)
        self._drv.duty_b(b_duty)
        
    @autoreply
    def phen_raw_a_duty(self, port, msg):
        _, duty = msg
        self._drv.phen_raw_a_duty(duty)

    @autoreply        
    def phen_raw_a_dir(self, port, msg):
        _, value = msg
        self._drv.phen_raw_a_dir(value)

    @autoreply
    def phen_raw_b_duty(self, port, msg):
        _, duty = msg
        self._drv.phen_raw_b_duty(duty)
        
    @autoreply
    def phen_raw_a_dir(self, port, msg):
        _, value = msg
        self._drv.phen_raw_b_dir(value)

def register(port):
    uipc.manager.register_server(port, RobotService())
