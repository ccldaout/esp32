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

    _hw_spi = {}

    def __new__(cls, id_,
                 *,
                 polarity,
                 phase,
                 bits,
                 baudrate,
                 mosi=None,
                 miso=None,
                 sck=None):

        if id_ in (ID_HSPI, ID_VSPI):
            hw_attr = (id_, polarity, phase, bits, baudrate)
            if hw_attr in cls._hw_spi:
                return cls._hw_spi[hw_attr]
            if id_ == ID_HSPI:
                mosi, miso, sck = HSPI_MOSI, HSPI_MISO, HSPI_SCK
            else:
                mosi, miso, sck = VSPI_MOSI, VSPI_MISO, VSPI_SCK
        elif id_ != ID_SOFT:
            raise TypeError('invalid id')
            
        self = super().__new__(cls)

        if mosi is not None:
            self.mosi = machine.Pin(mosi, machine.Pin.OUT)
        if miso is not None:
            self.miso = machine.Pin(miso, machine.Pin.IN)
        self.sck  = machine.Pin(sck,  machine.Pin.OUT)
        
        self.__spi = machine.SPI(id_,
                                 baudrate=baudrate,
                                 polarity=polarity,
                                 phase=phase,
                                 bits=bits,
                                 sck=self.sck,
                                 mosi=self.mosi,
                                 miso=self.miso)
        if id_ != ID_SOFT:
            cls._hw_spi[hw_attr] = self

        self.read = self.__spi.read
        self.readinto = self.__spi.readinto
        self.write = self.__spi.write
        self.write_readinto = self.__spi.write_readinto

        return self
