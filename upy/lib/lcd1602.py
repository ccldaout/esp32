import machine
import time


class LCD1602(object):

    __addr = 0x27

    def __init__(self, scl=33, sda=25):
        self.__i2c = machine.I2C(scl=machine.Pin(scl),
                                 sda=machine.Pin(sda))
        self.__buf = bytearray(1)

        # Entry Mode Set
        self.__putc_cursor_right = True
        self.__putc_shift_disp = False

        # Display ON/OFF
        self.__display = True
        self.__block_cursor = False
        self.__blink = False

        # Cursor or Display Shift
        self.__shift_disp = False	# False -> shift cursor
	self.__shift_right = False

        # Functin Set
        self.__8bit = False
        self.__2lines = True
        self.__5x10dot = False

    def _write4(self, is_data, val4):
        sleep_ns = time.sleep_ns
        writeto = self.__i2c.writeto
        addr = self.__addr
        buf = self.__buf

        rs = int(is_data) << 0
        rs_val4 = rs | (val4 << 4)

        buf[0] = rs
        writeto(addr, buf)
        sleep_ns(50)
        buf[0] = rs_val4 | (1<<2)	# Enable bit is ON
        writeto(addr, buf)
        sleep_ns(250)
        buf[0] = rs_val4		# Enable bit if OFF
        writeto(addr, buf)
        sleep_ns(50)
        buf[0] = 0
        writeto(addr, buf)
        sleep_ns(200)

    def cmd(self, b8):
        self._write4(False, b8 >> 4)
        self._write4(False, b8 & 0xf)

    def clear_display(self):
        self.cmd((1<<0))

    def return_home(self):
        self.cmd((1<<1))

    def entry_mode(self, cursor_right=None, shift_disp=None):
        if cursor_right is None:
            cursor_right = self.__putc_cursor_right
        if shift_disp is None:
            shift_disp = self.__putc_shift_disp
        cmd = (1<<2) | (int(cursor_right) << 1) | (int(shift_disp) << 0)
        self.cmd(cmd)

    def display(self, display=None, block_cursor=None, blink=None):
        if display is None:
            display = self.__display
        if block_cursor is None:
            block_cursor = self.__block_cursor
        if blink is None:
            blink = self.__blink
        cmd = (1<<3) | (int(display) << 2) | (int(block_cursor) << 1) | (int(blink) << 0)
        self.cmd(cmd)

    def shift(self, display=None, to_right=None):
        if display is None:
            display = self.__shift_disp
        if to_right is None:
            to_right = self.__shift_right
        cmd = (1<<4) | (int(display) << 3) | (int(to_right) << 2)
        self.cmd(cmd)

    def function(self, double_line=None, big_font=None):
        bit8 = self.__8bit
        if double_line is None:
            double_line = self.__2lines
        if big_font is None:
            big_font = self.__5x10dot
        cmd = (1<<5) | (int(bit8) << 4) | (int(double_line) << 3) | (int(big_font) << 2)
        self.cmd(cmd)

    def cgram(self, addr):
        cmd = (1<<6) | addr
        self.cmd(cmd)

    def ddram(self, addr):
        cmd = (1<<7) | addr
        self.cmd(cmd)

    def data(self, b8):
        self._write4(True, b8 >> 4)
        self._write4(True, b8 & 0xf)

    def init(self):
        sleep_ms = time.sleep_ms
        sleep_ms(50)
        self._write4(False, 0x3)
        sleep_ms(5)
        self._write4(False, 0x3)
        sleep_ms(1)
        self._write4(False, 0x3)
        self._write4(False, 0x2)	# become 4-bit mode

        # ...
