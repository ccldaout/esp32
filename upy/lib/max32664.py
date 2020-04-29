import machine
import time

class MAX32664(object):

    __addr = 0x55
    __delay_enable_ms = 45
    __delay_cmd_ms = 6

    def __init__(self, scl=22, sda=21, rst=32, mfio=33):
        self.__i2c = machine.I2C(scl=machine.Pin(scl),
                                 sda=machine.Pin(sda))
        self.__mfio = machine.Pin(mfio, machine.Pin.OUT, 1)
        self.__rst = machine.Pin(rst, machine.Pin.OUT)
        self.__rst.value(1)
        self.__rst.value(0)
        time.sleep_ms(10)
        self.__rst.value(1)
        time.sleep_ms(1000)
        self.__mfio.init(machine.Pin.IN, machine.Pin.PULL_UP)

    def init(self):
        self.__cmd('\x02\x00')
        b = self.__read_byte()
        if b != 0:
            raise Exception('Unexpceted Device Mode: %d' % b)

        # Set Output Mode
        self.__cmd('\x10\x00\x02')
        b = self.__read_byte()
        print('Set Output Mode:', b)

        # Set FIFO Threshold
        self.__cmd('\x10\x01\x01')
        b = self.__read_byte()
        print('Set FIFO Threshold:', b)

        # Enable AGC algorithm
        self.__enable('\x52\x00\x01')
        b = self.__read_byte()
        print('Enable AGC algorithm:', b)

        # Enable MAX30101 sensor
        self.__enable('\x44\x03\x01')
        b = self.__read_byte()
        print('Enable MAX30101 sensor:', b)

	# Enable MaximFast algorithm
        self.__enable('\x52\x02\x01')
        b = self.__read_byte()
        print('Enable MaximFast algorithm:', b)

        # Read # of samples to avgerage
        self.__cmd('\x51\x00\x03')
        b = self.__read_byte()
        print('Read # of samples to avgerage', b)

        time.sleep(1)

    def __cmd(self, bs):
        self.__i2c.writeto(self.__addr, bs, True)
        time.sleep_ms(self.__delay_cmd_ms)

    def __enable(self, bs):
        self.__i2c.writeto(self.__addr, bs, True)
        time.sleep_ms(self.__delay_enable_ms)

    def __read_byte(self):
        bs = self.__i2c.readfrom(self.__addr, 1, True)
        return int(bs[0])

    def read(self):
        # Read sensor hub status
        self.__cmd('\x00\x00')
        b = self.__read_byte()
        if b != 0:
            raise Exception('Unexpceted Sensor HUB status: %d' % b)

        # Read # of samples available in the FIFO
        self.__cmd('\x12\x00')
        b = self.__read_byte()
        print('Read # of samples available in the FIFO', b)

        # Read data stored in output FIFO
        self.__cmd('\x12\x01')
        bs = self.__i2c.readfrom(self.__addr, 6, True)
        return bs

mx = MAX32664()
mx.init()
