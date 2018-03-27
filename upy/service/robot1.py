import os
import machine
import time

import mipc
import drv8835
from config.service_robot1 import config


@mipc.autoreply
class RobotService(mipc.ServiceBase):

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

    @mipc.autoreply
    def enable(self):
        if not self._enabled:
            self._drv = drv8835.DRV8835(config.drv8835_mode,
                                        config.A_in1, config.A_in2,
                                        config.B_in1, config.B_in2)
            self._enabled = True
            self._logger('drv8835 is enabled.')
        else:
            self._logger('drv8835 is already enabled.')

    @mipc.autoreply
    def duty(self, a_duty, b_duty):
        self._drv.duty_a(a_duty)
        self._drv.duty_b(b_duty)
        
    @mipc.autoreply
    def phen_raw_a_duty(self, duty):
        self._drv.phen_raw_a_duty(duty)

    @mipc.autoreply
    def phen_raw_a_dir(self, value):
        self._drv.phen_raw_a_dir(value)

    @mipc.autoreply
    def phen_raw_b_duty(self, duty):
        self._drv.phen_raw_b_duty(duty)
        
    @mipc.autoreply
    def phen_raw_a_dir(self, value):
        self._drv.phen_raw_b_dir(value)


def register():
    mipc.manager.register_server(config.port, RobotService())
    return config.port
