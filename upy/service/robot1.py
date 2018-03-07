import os
import machine
import time

import uipc
import drv8835
from config import robot as config


@uipc.autoreply
class RobotService(uipc.ServiceBase):

    def __init__(self):
        from display import text_board
        self._logger = text_board.putline
        self._drv = None
        self._enabled = False

    def on_accepted(self, port):
        self._logger('on_accepted')

    def on_disconnected(self, port):
        self._logger('on_disconnected')

    def on_exception(self, port):
        self._logger('on_exception')

    @uipc.autoreply
    def enable(self):
        if not self._enabled:
            self._drv = drv8835.DRV8835(config.drv8835_mode,
                                        config.A_in1, config.A_in2,
                                        config.B_in1, config.B_in2)
            self._enabled = True
            self._logger('drv8835 is enabled.')
        else:
            self._logger('drv8835 is already enabled.')

    @uipc.autoreply
    def duty(self, a_duty, b_duty):
        self._drv.duty_a(a_duty)
        self._drv.duty_b(b_duty)
        
    @uipc.autoreply
    def phen_raw_a_duty(self, duty):
        self._drv.phen_raw_a_duty(duty)

    @uipc.autoreply
    def phen_raw_a_dir(self, value):
        self._drv.phen_raw_a_dir(value)

    @uipc.autoreply
    def phen_raw_b_duty(self, duty):
        self._drv.phen_raw_b_duty(duty)
        
    @uipc.autoreply
    def phen_raw_a_dir(self, value):
        self._drv.phen_raw_b_dir(value)


def register(port):
    uipc.manager.register_server(port, RobotService())
