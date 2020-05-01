import machine
import time


class BPM(object):
    def __init__(self, ba):
        self.heart_rate = ((ba[0] << 8)|ba[1]) * 0.1
        self.confidence = ba[2]
        self.SpO2 = ((ba[3] << 8)|ba[4]) * 0.1
        self.status = ba[5]

    def __repr__(self):
        return "BPM(heart_rate:%f, confidence:%d%%, SpO2:%f%%, status:%d)" % (
            self.heart_rate, self.confidence, self.SpO2, self.status
        )

    __str__ = __repr__


class MAX32664(object):

    __addr = 0x55
    __delay_enable_ms = 45
    __delay_cmd_ms = 6

    def __init__(self, scl=33, sda=25, rst=32, mfio=26):
        self.__i2c = machine.I2C(scl=machine.Pin(scl),
                                 sda=machine.Pin(sda))
        self.__mfio = machine.Pin(mfio, machine.Pin.OUT)
        self.__rst = machine.Pin(rst, machine.Pin.OUT)
        self.__mfio.value(1)
        self.__rst.value(1)
        self.__rst.value(0)
        time.sleep_ms(10)
        self.__rst.value(1)
        time.sleep_ms(1000)
        self.__mfio.init(machine.Pin.IN, machine.Pin.PULL_UP)

    def init(self):
        self._cmd([0x02, 0x00])
        b = self._readstatus()
        if b != 0:
            raise Exception('Unexpceted Device Mode: %d' % b)

        # Set Output Mode
        self._cmd([0x10, 0x00, 0x02])
        s = self._readstatus()
        print('Set Output Mode:', s)

        # Set FIFO Threshold
        self._cmd([0x10, 0x01, 0x01])
        s = self._readstatus()
        print('Set FIFO Threshold:', s)

        # Enable AGC algorithm
        self._enable([0x52, 0x00, 0x01])
        s = self._readstatus()
        print('Enable AGC algorithm:', s)

        # Enable MAX30101 sensor
        self._enable([0x44, 0x03, 0x01])
        s = self._readstatus()
        print('Enable MAX30101 sensor:', s)

	# Enable MaximFast algorithm
        self._enable([0x52, 0x02, 0x01])
        s = self._readstatus()
        print('Enable MaximFast algorithm:', s)

        # Read # of samples to avgerage
        self._cmd([0x51, 0x00, 0x03])
        s, n = self._readreply(1)
        print('Read # of samples to avgerage', s, n)

        time.sleep(1)

    def _cmd(self, bs):
        self.__i2c.writeto(self.__addr, bytes(bs), True)
        time.sleep_ms(self.__delay_cmd_ms)

    def _enable(self, bs):
        self.__i2c.writeto(self.__addr, bytes(bs), True)
        time.sleep_ms(self.__delay_enable_ms)

    def _readstatus(self):
        bs = self.__i2c.readfrom(self.__addr, 1, True)
        return int(bs[0])

    def _readreply(self, n=1):
        res = self.__i2c.readfrom(self.__addr, n+1, True)
        if n == 1:
            return res[0], res[1]
        else:
            return res[0], res[1:]

    def get(self):
        # Read sensor hub status
        while True:
            self._cmd([0x00, 0x00])
            s, r = self._readreply()
            if s != 0:
                raise Exception('Unexpected read status: %d' % s)
            if (r & 0x1) != 0:
                raise Exception('Unexpceted Sensor HUB status: %d' % r)
            if (r & 0x8) != 0:
                break
            time.sleep_ms(100)

        ### Read # of samples available in the FIFO
        ##self._cmd([0x12, 0x00])
        ##s, r = self._readreply()
        ##print('Read # of samples available in the FIFO', r)

        # Read data stored in output FIFO
        self._cmd([0x12, 0x01])
        time.sleep_ms(10)
        s, rv = self._readreply(6)
        return BPM(rv)

    @property
    def mfio(self):
        return self.__mfio()
