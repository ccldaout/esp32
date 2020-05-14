# -*- coding: utf-8 -*-

import array
import machine
from collections import namedtuple as _ntuple

_IO_W = 0
_IO_R = (1<<7)
_IO_MB = (1<<6)

_REG_DEVID = 0x00
_REG_OFSX = 0x1E
_REG_OFSY = 0x1F
_REG_OFSZ = 0x20
_REG_BW_RATE = 0x2C
_REG_POWER_CTL = 0x2D
_REG_DATA_FORMAT = 0x31
_REG_DATAX0 = 0x32
_REG_DATAX1 = 0x33
_REG_DATAY0 = 0x34
_REG_DATAY1 = 0x35
_REG_DATAZ0 = 0x36
_REG_DATAZ1 = 0x37
_REG_FIFO_CTL = 0x38
_REG_FIFO_STATUS = 0x39

def _int16(ui16):
    return -(ui16 & 0x8000)|(ui16 & 0x7fff)

class ADXL345(object):

    BW_RATE = _ntuple('BW_RATE', ('low_power', 'rate'))
    POWER_CTL = _ntuple('POWER_CTL', ('link', 'auto_sleep', 'measure', 'sleep', 'wakeup'))
    DATA_FORMAT = _ntuple('DATA_FORMAT', ('self_test', 'spi', 'int_invert',
                                          'full_res', 'justify', 'range_'))
    FIFO_CTL = _ntuple('FIFO_CTL', ('fifo_mode', 'trigger', 'samples'))
    FIFO_STATUS = _ntuple('FIFO_STATUS', ('fifo_trig', 'entries'))

    def __init__(self, spi, cs_num):
        self._cs = machine.Pin(cs_num, machine.Pin.OUT)
        self._cs.value(1)
        self._spi = spi
        self._buf = array.array('B', (0 for _ in range(6)))
        self._mv = memoryview(self._buf)

    def read(self, reg, n=1):
        reg |= _IO_R
        if n > 1:
            reg |= _IO_MB
        self._cs.value(0)
        buf = self._spi.read(n+1, reg)
        self._cs.value(1)
        return buf[1] if n == 1 else buf[1:]

    def write(self, reg, buf):
        reg |= _IO_W
        if len(buf) > 1:
            reg |= _IO_MB
        self._cs.value(0)
        self._spi.read(1, reg)
        self._spi.write(buf)
        self._cs.value(1)

    def read_devid(self):
        return self.read(_REG_DEVID)

    def read_offsets(self):
        v = self.read(_REG_OFSX, 3)
        return (v[0], v[1], v[2])

    def write_offset_x(self, x):
        self._mv[0] = x
        self.write(_REG_OFSX, self._mv[:1])

    def write_offset_y(self, y):
        self._mv[0] = y
        self.write(_REG_OFSY, self._mv[:1])

    def write_offset_z(self, z):
        self._mv[0] = z
        self.write(_REG_OFSZ, self._mv[:1])

    def read_bw_rate(self):
        v = self.read(_REG_BW_RATE)
        return self.BW_RATE((0x10 & v) >> 4,
                            (0x0f & v) >> 0)

    def write_bw_rate(self, low_power=0, rate=0x0A):
        self._mv[0] = ((low_power << 4) |
                       (rate        << 0))
        return self.write(_REG_BW_RATE, self._mv[:1])
    
    def read_power_ctl(self):
        v = self.read(_REG_POWER_CTL)
        return self.POWER_CTL((0x20 & v) >> 5,
                              (0x10 & v) >> 4,
                              (0x08 & v) >> 3,
                              (0x04 & v) >> 2,
                              (0x03 & v) >> 0)

    def write_power_ctl(self, link=0, auto_sleep=0, measure=1, sleep=0, wakeup=0):
        self._mv[0] = ((link       << 5) |
                       (auto_sleep << 4) |
                       (measure    << 3) |
                       (sleep      << 2) |
                       (wakeup     << 0))
        self.write(_REG_POWER_CTL, self._mv[:1])

    def read_data_format(self):
        v = self.read(_REG_DATA_FORMAT)
        return self.DATA_FORMAT((0x80 & v) >> 7,
                                (0x40 & v) >> 6,
                                (0x20 & v) >> 5,
                                (0x08 & v) >> 3,
                                (0x04 & v) >> 2,
                                (0x03 & v) >> 0)

    def write_data_format(self, self_test=0, spi=0,
                          int_invert=0, full_res=1, justify=0, range_=0):
        self._mv[0] = ((self_test  << 7) |
                       (spi        << 6) |
                       (int_invert << 5) |
                       (full_res   << 3) |
                       (justify    << 2) |
                       (range_     << 0))
        self.write(_REG_DATA_FORMAT, self._mv[:1])

    def read_data(self):
        v = self.read(_REG_DATAX0, 6)
        return (_int16((v[1] << 8) | v[0]),
                _int16((v[3] << 8) | v[2]),
                _int16((v[5] << 8) | v[4]))

    def read_fifo_ctl(self):
        v = self.read(_REG_FIFO_CTL)
        return self.FIFO_CTL((0xC0 & v) >> 6,
                             (0x20 & v) >> 5,
                             (0x1F & v) >> 0)

    def write_fifo_ctl(self, fifo_mode=0, trigger=0, samples=0):
        self._mv[0] = ((fifo_mode << 6) |
                       (trigger   << 5) |
                       (samples   << 0))
        self.write(_REG_FIFO_CTL, self._mv[:1])
        
    def read_fifo_status(self):
        v = self.read(_REG_FIFO_STATUS)
        return self.FIFO_STATUS((0x80 & v) >> 7,
                                (0x2f & v) >> 0)

import spi
vspi = spi.SPI(spi.ID_VSPI, polarity=1, phase=1,
               bits=8, baudrate=6*1000*1000)

ad = ADXL345(vspi, 32)
ad.write_power_ctl()
