import machine
import time


class IOBase(object):

    def write4(self, is_data, val4):
        raise NotImplementedError()


class PCF8574(IOBase):

    def __init__(self, addr=0x27, scl=33, ada=25):
        self.__addr = addr
        self.__i2c = machine.I2C(scl=machine.Pin(scl),
                                 sda=machine.Pin(sda),
                                 freq=100000)
        self.__buf = bytearray(1)

    def write4(self, is_data, val4):
        sleep_us = time.sleep_us
        writeto = self.__i2c.writeto
        addr = self.__addr
        buf = self.__buf

        bl = int(self.backlight) << 3
        rs = int(is_data) << 0
        rs_val4 = rs | (val4 << 4)

        buf[0] = bl | rs
        writeto(addr, buf)
        sleep_us(1)			# >= 50ns
        buf[0] = bl | rs_val4 | (1<<2)	# Enable bit is ON
        writeto(addr, buf)
        sleep_us(1)			# >= 250ns
        buf[0] = bl | rs_val4		# Enable bit if OFF
        writeto(addr, buf)
        sleep_us(1)			# >= 50ns
        buf[0] = bl
        writeto(addr, buf)
        sleep_us(1)			# >= 200ns


class GPIO(IOBase):

    def __init__(self, rs=19, rw=18, en=5, d4_7=(33, 25, 26, 27)):
        self.__pins = (machine.Pin(rs, machine.Pin.OUT),
                       machine.Pin(rw, machine.Pin.OUT),
                       machine.Pin(en, machine.Pin.OUT),
                       machine.Pin(d4_7[0], machine.Pin.OUT),	# D4
                       machine.Pin(d4_7[1], machine.Pin.OUT),	# D5
                       machine.Pin(d4_7[2], machine.Pin.OUT),	# D6
                       machine.Pin(d4_7[3], machine.Pin.OUT))	# D7

    def write4(self, is_data, val4):
        sleep_us = time.sleep_us
        rs, rw, en, d4, d5, d6, d7 = self.__pins

        en.value(0)			# 0:disable
        rs.value(int(is_data)))		# 0:command, 1:data
        rw.value(0)			# 0:write
        sleep_us(1)			# >= 50ns

        en.value(1)			# 1:enable
        d4.value((val4 & 0x1))
        val4 >>= 1
        d5.value((val4 & 0x1))
        val4 >>= 1
        d6.value((val4 & 0x1))
        val4 >>= 1
        d7.value((val4 & 0x1))
        sleep_us(1)			# >= 80ns

        en.value(0)
        sleep_us(1)			# >= 10ns


class HD44780(object):

    def __init__(self, io):
        self.__io = io
        self._write4 = io.write4

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

        self.backlight = True

    def cmd(self, b8):
        self._write4(False, b8 >> 4)
        self._write4(False, b8 & 0xf)
        return self

    def clear_display(self):
        self.cmd((1<<0))
        return self

    def return_home(self):
        self.cmd((1<<1))
        time.sleep_us(1520)
        return self

    def entry_mode(self, cursor_right=None, shift_disp=None):
        if cursor_right is None:
            cursor_right = self.__putc_cursor_right
        if shift_disp is None:
            shift_disp = self.__putc_shift_disp
        cmd = (1<<2) | (int(cursor_right) << 1) | (int(shift_disp) << 0)
        self.cmd(cmd)
        time.sleep_us(37)
        return self

    def display(self, display=None, block_cursor=None, blink=None):
        if display is None:
            display = self.__display
        if block_cursor is None:
            block_cursor = self.__block_cursor
        if blink is None:
            blink = self.__blink
        cmd = (1<<3) | (int(display) << 2) | (int(block_cursor) << 1) | (int(blink) << 0)
        self.cmd(cmd)
        time.sleep_us(37)
        return self

    def shift(self, display=None, to_right=None):
        if display is None:
            display = self.__shift_disp
        if to_right is None:
            to_right = self.__shift_right
        cmd = (1<<4) | (int(display) << 3) | (int(to_right) << 2)
        self.cmd(cmd)
        time.sleep_us(37)
        return self

    def function(self, double_line=None, big_font=None):
        bit8 = self.__8bit
        if double_line is None:
            double_line = self.__2lines
        if big_font is None:
            big_font = self.__5x10dot
        cmd = (1<<5) | (int(bit8) << 4) | (int(double_line) << 3) | (int(big_font) << 2)
        self.cmd(cmd)
        time.sleep_us(37)
        return self

    def cgram(self, addr):
        cmd = (1<<6) | addr
        self.cmd(cmd)
        time.sleep_us(37)
        return self

    def ddram(self, addr):
        cmd = (1<<7) | addr
        self.cmd(cmd)
        time.sleep_us(37)
        return self

    def data(self, b8):
        self._write4(True, b8 >> 4)
        self._write4(True, b8 & 0xf)
        time.sleep_us(37)
        return  self

    def puts(self, row, col, s):
        if row != 0:
            col += 40
        self.ddram(col)
        for c in s:
            self.data(ord(c))
        return self

    def init(self):
        sleep_ms = time.sleep_ms
        sleep_ms(50)
        self._write4(False, 0x3)
        sleep_ms(5)
        self._write4(False, 0x3)
        sleep_ms(1)
        self._write4(False, 0x3)
        self._write4(False, 0x2)	# become 4-bit mode

        self.function()
        self.display(display=False, block_cursor=False, blink=False)
        self.clear_display()
        self.entry_mode()

        return self

    def test(self):
        self.puts(0, 0, 'Hello')
        self.puts(1, 2, 'World !!')
        return self
