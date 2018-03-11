import os
import machine
import time

import uipc
import drv8835
import sensor
from config.service_robot2 import config


class Mutext(object):
    def __init__(self):
        self._lock = _thread.allocate_lock()
        self.acquire = self._lock.acquire
        self.release = self._lock.release

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.release()

    def __call__(self, f):
        def wrapper(*args, **kwargs):
            with self._lock:
                return f(*args, **kwargs)
        return wrapper

_mutex = Mutex()

class Robot(object):
    def __init__(self):
        from display import text_board
        self._logger = text_board.putline
        self._drv = None
        self._sensor = None
        # idle, ready, searching, found, notfound, tracing, lost
        self._status = 'idle'
        self._stop_request = False

    @property
    def status(self):
        with _mutex:
            return self._status

    @_mutex
    def enable(self):
        if self._status == 'idle':
            self._drv = drv8835.DRV8835(config.drv8835_mode,
                                        config.A_in1, config.A_in2,
                                        config.B_in1, config.B_in2)
            self._sensor = sensor.QTRxRC(config.qtr3rc_pins)
            self._logger('drv8835/QTR3RC is enabled.')
        else:
            self._logger('drv8835/QTR3RC is already enabled.')
        self._status = 'ready'

    def _search_line(self):
        pass

    def _trace_line(self):
        pass

    @_mutex
    def start_searching(self):
        if self._status != 'ready':
            return False
        pass

    @_mutex
    def start_tracing(self):
        if self._status != 'found':
            return False
        pass

    @_mutex
    def stop(self):
        self._stop_request = True

    @_mutex
    def duty(self, a_duty, b_duty):
        self._drv.duty_a(a_duty)
        self._drv.duty_b(b_duty)
        
@uipc.autoreply
class RobotService(uipc.ServiceBase):

    def __init__(self):
        self._robot = Robot()

    def on_accepted(self, port):
        self._logger('on_accepted')

    def on_disconnected(self, port):
        self._logger('on_disconnected')

    def on_exception(self, port):
        self._logger('on_exception')

    @uipc.autoreply
    def enable(self):
        self._robot.enable()

    @uipc.autoreply
    def status(self):
        return self._robot.status

    @uipc.autoreply
    def start_search(self):
        pass

    @uipc.autoreply
    def start_trace(self):
        pass

    @uipc.autoreply
    def stop(self):
        pass

def register():
    uipc.manager.register_server(config.port, RobotService())
    return config.port
