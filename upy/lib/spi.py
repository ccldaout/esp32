import machine

ID_HSPI = 1
ID_VSPI = 2
ID_SOFT = -1

VSPI_MOSI = 23
VSPI_MISO = 19
VSPI_SCK = 18
VSPI_SS = 5

HSPI_MOSI = 13
HSPI_MISO = 12
HSPI_SCK = 14
HSPI_SS = 15

class SPI(object):

    HSPI = None
    VSPI = None
    SOFT_SPI = None

    def __new__(cls, id,
                 *,
                 polarity = 1,
                 phase = 1,
                 mosi=None,
                 miso=None,
                 sck=None,
                 bits=8,
                 baudrate = 6*1000*1000):	# 6MHz

        if id == ID_HSPI:
            if cls.HSPI:
                return cls.HSPI
            mosi, miso, sck, ss = HSPI_MOSI, HSPI_MISO, HSPI_SCK, HSPI_SS
        elif id == ID_VSPI:
            if cls.VSPI:
                return cls.VSPI
            mosi, miso, sck, ss = VSPI_MOSI, VSPI_MISO, VSPI_SCK, VSPI_SS
        elif id == ID_SOFT:
            if cls.SOFT_SPI:
                return cls.SOFT_SPI
            ss = None
        else:
            raise TypeError('invalid id')
            
        self = super().__new__(cls)

        self.mosi = machine.Pin(mosi, machine.Pin.OUT)
        self.miso = machine.Pin(miso, machine.Pin.IN)
        self.sck  = machine.Pin(sck,  machine.Pin.OUT)
        if ss is not None:
            self.ss_number = ss
        
        if id == ID_SOFT:
            # when id is ID_SOFT, initializer require sck/mosi/miso arguments.
            self.__spi = machine.SPI(id,
                                     baudrate=baudrate,
                                     polarity=polarity,
                                     phase=phase,
                                     sck=self.sck,
                                     mosi=self.mosi,
                                     miso=self.miso,
                                     bits=bits)
        else:
            # when id is not ID_SOFT, initialize refuse sck/mosi/miso arguments.
            self.__spi = machine.SPI(id,
                                     baudrate=baudrate,
                                     polarity=polarity,
                                     phase=phase,
                                     bits=bits)
            self.__spi.init(mosi=self.mosi, miso=self.miso, sck=self.sck)

        if id == ID_HSPI:
            cls.HSPI = self
        elif id == ID_VSPI:
            cls.VSPI = self
        elif id == ID_SOFT:
            cls.SOFT_SPI = self

        self.read = self.__spi.read
        self.readinto = self.__spi.readinto
        self.write = self.__spi.write
        self.write_readinto = self.__spi.write_readinto

        return self
