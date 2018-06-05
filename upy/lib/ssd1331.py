import array
import machine
import spi
import sys
import time
from display import *
from config.ssd1331 import config


#----------------------------------------------------------------------------
#                              display driver
#----------------------------------------------------------------------------

class SSD1331(object):

    WIDTH = 96
    HEIGHT = 64

    def __init__(self, *,
                 spi,
                 pinnum_cs,		# Chip Select
                 pinnum_dc,		# Data/Command
                 pinnum_rst):		# Reset
        self._spi = spi
        self._cs = machine.Pin(pinnum_cs, machine.Pin.OUT)
        self._dc = machine.Pin(pinnum_dc, machine.Pin.OUT)
        self._rst = machine.Pin(pinnum_rst, machine.Pin.OUT)

        self._cs.value(1)
        self._rst.value(1)
        self._buf = array.array('B', (0 for _ in range(64)))
        self._pixbuf = None
        self.rgb_max = (0, 0, 0)
        self.rgb_bits = (0, 0, 0)
        self._disp_on = False
        self._disp_sw_tv_ms = 0
        if config.pin_sw is not None:
            self._disp_sw = machine.Pin(36, machine.Pin.IN, machine.Pin.PULL_DOWN)
            self._disp_sw.irq(self._toggle_display, machine.Pin.IRQ_FALLING)
        self._RMCD = 0

        # for performance
        self._spi_write = self._spi.write
        self._cs_value = self._cs.value
        self._dc_value = self._dc.value
        self.command = self._command
        self.send_pixels = self._send_pixels

    # display on/off switch
    def _toggle_display(self, *args):
        t = time.ticks_ms()
        if t < self._disp_sw_tv_ms:
            return
        self._disp_sw_tv_ms = t + 500
        if self._disp_on:
            self.set_display_off()
        else:
            self.set_display_on()

    # SPI interface

    def _command(self, buf, size):
        self._cs_value(0)
        self._dc_value(0)
        self._spi_write(memoryview(buf)[:size])
        self._cs_value(1)

    def _send_pixels(self, buf, size):
        self._cs_value(0)
        self._dc_value(1)
        self._spi_write(memoryview(buf)[:size])
        self._cs_value(1)

    # support methods

    def _pixel_256(self, r, g, b):
        self._pixbuf[0] = ((0x7 & r)<<5)|((0x7 & g)<<2)|(0x3 & b)
        return self._pixbuf

    def _pixel_65k1(self, r, g, b):
        self._pixbuf[0] = ((0x1f & r)<<3)|((0x3f & g)>>3)
        self._pixbuf[1] = ((0x7 & g)<<5)|(0x1f & b)
        return self._pixbuf

    def _pixel_65k2(self, r, g, b):
        self._pixbuf[0] = r<<1
        self._pixbuf[1] = g
        self._pixbuf[2] = b<<1
        return self._pixbuf

    def _hook_color_format(self, color_format):
        if color_format == 0:
            self.pixel = self._pixel_256
            self._pixbuf = array.array('B', (0,))
            self.rgb_max = (0x3, 0x7, 0x7)
            self.rgb_bits = (2, 3, 3)
        elif color_format == 1:
            self.pixel = self._pixel_65k1
            self._pixbuf = array.array('B', (0, 0))
            self.rgb_max = (0x1f, 0x3f, 0x1f)
            self.rgb_bits = (5, 6, 5)
        elif color_format == 2:
            self.pixel = self._pixel_65k2
            self._pixbuf = array.array('B', (0, 0, 0))
            self.rgb_max = (0x1f, 0x3f, 0x1f)
            self.rgb_bits = (5, 6, 5)

    # display initializer

    def init(self):
        self._rst.value(0)
        time.sleep(0.000003)
        self._rst.value(1)
        time.sleep(0.000003)
        self.set_master_configuration(external_Vcc_supply=True)
        time.sleep(0.01)
        self.clear()
        self.set_enable_linear_grayscale_table()
        self.set_multiplex_ratio()
        self.set_remap_and_color_depth(color_format=config.color_format,
                                       split_COM_odd_even=config.split_COM_odd_even,
                                       color_BGR_order=config.color_BGR_order)
        self.set_display_on()
        time.sleep(0.1)

    # SSD1331 primitive command

    def set_column_address(self, start=0, end=95):
        b = self._buf
        b[0] = 0x15
        b[1] = start
        b[2] = end
        self.command(b, 3)

    def set_row_address(self, start=0, end=63):
        b = self._buf
        b[0] = 0x75
        b[1] = start
        b[2] = end
        self.command(b, 3)
        
    def set_contrast_A(self, contrast=128):
        b = self._buf
        b[0] = 0x81
        b[1] = contrast
        self.command(b, 2)

    def set_contrast_B(self, contrast=128):
        b = self._buf
        b[0] = 0x82
        b[1] = contrast
        self.command(b, 2)

    def set_contrast_C(self, contrast=128):
        b = self._buf
        b[0] = 0x83
        b[1] = contrast
        self.command(b, 2)

    def master_current_control(self, attenuation=15):
        b = self._buf
        b[0] = 0x87
        b[1] = attenuation
        self.command(b, 2)

    def set_second_precharge_speed(self, speed_A, speed_B, speed_C):
        b = self._buf
        b[0] = 0x8A
        b[1] = speed_A
        b[2] = 0x8B
        b[3] = speed_B
        b[4] = 0x8C
        b[5] = speed_C
        self.command(b, 6)

    def set_remap_and_color_depth(self, **kwargs):
        attrs = (('vertical_address_increment', 0, 1),
                 ('column_reverse_order', 1, 1),
                 ('color_BGR_order', 2, 1),
                 ('left_right_swap_on_COM', 3, 1),
                 ('scan_reverse_on_COM', 4, 1),
                 ('split_COM_odd_even', 5, 1),
                 ('color_format', 6, 0x3))
        f = self._RMCD
        for name, pos, mask in attrs:
            v = kwargs.pop(name, None)
            if v is not None:
                f &= ~(mask << pos)
                f |= (int(v) << pos)
                fn = '_hook_' + name
                if hasattr(self, fn):
                    getattr(self, fn)(v)
        if kwargs:
            raise TypeError('unexpected keyword arguments: %s' % kwargs)

        self._RMCD = f
        b = self._buf
        b[0] = 0xA0
        b[1] = self._RMCD
        self.command(b, 2)

    def set_display_start_line(self, start=0):
        b = self._buf
        b[0] = 0xA1
        b[1] = start
        self.command(b, 2)
        
    def set_display_offset(self, offset=0):
        b = self._buf
        b[0] = 0xA2
        b[1] = offset
        self.command(b, 2)
        
    def set_normal_display(self):
        b = self._buf
        b[0] = 0xA4
        self.command(b, 1)

    def set_entire_display_on(self):
        b = self._buf
        b[0] = 0xA5
        self.command(b, 1)

    def set_entire_display_off(self):
        b = self._buf
        b[0] = 0xA6
        self.command(b, 1)

    def set_inverse_display(self):
        b = self._buf
        b[0] = 0xA7
        self.command(b, 1)

    def set_multiplex_ratio(self, mux_ratio=63):
        b = self._buf
        b[0] = 0xA8
        b[1] = mux_ratio
        self.command(b, 2)

    def dim_mode_setting(self, *, contrast_A, contrast_B, contrast_C,
                         precharge_volt):
        b = self._buf
        b[0] = 0xAB
        b[1] = 0	# Reserved
        b[2] = contrast_A
        b[3] = contrast_B
        b[4] = contrast_C
        b[5] = precharge_volt
        self.command(b, 6)

    def set_master_configuration(self, *, external_Vcc_supply):
        b = self._buf
        b[0] = 0xAD
        b[1] = 0x8E | int(not external_Vcc_supply)
        self.command(b, 2)

    def set_display_dim(self):
        b = self._buf
        b[0] = 0xAC
        self.command(b, 1)

    def set_display_off(self):
        self._disp_on = False
        b = self._buf
        b[0] = 0xAE
        self.command(b, 1)

    def set_display_on(self):
        self._disp_on = True
        b = self._buf
        b[0] = 0xAF
        self.command(b, 1)

    def set_power_save_mode(self, enable):
        b = self._buf
        b[0] = 0xB0
        b[1] = int(bool(enable))
        self.command(b, 2)

    def period_adjustment(self, ph1_period=4, ph2_period=7):
        b = self._buf
        b[0] = 0xB1
        b[1] = (ph2_period << 4)|ph1_period
        self.command(b, 2)

    def divratio_and_oscfreq(self, divratio=0, oscfreq=0xd):
        b = self._buf
        b[0] = 0xB3
        b[1] = (oscfreq << 4)|divratio
        self.command(b, 2)
        
    def set_grayscale_table(self, pulse_width_list):
        b = self._buf
        b[0] = 0xB8
        b[1:33] = array.array('B', pulse_width_list)
        self.command(b, 33)

    def set_enable_linear_grayscale_table(self):
        b = self._buf
        b[0] = 0xB9
        self.command(b, 1)

    def set_precharge_level(self, code=0x1f):
        b = self._buf
        b[0] = 0xB8
        b[1] = code << 1
        self.command(b, 2)

    def set_Vcomh(self, code=0x1f):
        b = self._buf
        b[0] = 0xBE
        b[1] = code << 1
        self.command(b, 2)

    def set_command_lock(self, enable):
        b = self._buf
        b[0] = 0xFD
        b[1] = 0x12 | (int(bool(enable)) << 1)
        self.command(b, 2)

    # SSD1331 graphics command

    def draw_line(self,
                  col_start, row_start,
                  col_end, row_end,
                  color_C_line,
                  color_B_line,
                  color_A_line):
        b = self._buf
        b[0] = 0x21
        b[1] = col_start
        b[2] = row_start
        b[3] = col_end
        b[4] = row_end
        b[5] = color_C_line << 1
        b[6] = color_B_line
        b[7] = color_A_line << 1
        self.command(b, 8)
                  
    def draw_rectangle(self,
                       col_start, row_start,
                       col_end, row_end,
                       color_C_line,
                       color_B_line,
                       color_A_line,
                       color_C_area,
                       color_B_area,
                       color_A_area):
        b = self._buf
        b[0] = 0x22
        b[1] = col_start
        b[2] = row_start
        b[3] = col_end
        b[4] = row_end
        b[5] = color_C_line << 1
        b[6] = color_B_line
        b[7] = color_A_line << 1
        b[8] = color_C_area << 1
        b[9] = color_B_area
        b[10] = color_A_area << 1
        self.command(b, 11)

    def copy(self,
             col_start, row_start,
             col_end, row_end,
             new_col_start, new_row_start):
        b = self._buf
        b[0] = 0x23
        b[1] = col_start
        b[2] = row_start
        b[3] = col_end
        b[4] = row_end
        b[5] = new_col_start
        b[6] = new_row_start
        self.command(b, 7)
        
    def clear(self,
              col_start=0, row_start=0,
              col_end=95, row_end=63):
        b = self._buf
        b[0] = 0x25
        b[1] = col_start
        b[2] = row_start
        b[3] = col_end
        b[4] = row_end
        self.command(b, 5)

    def enable_fill(self, enable_fill=True, enable_reverse_in_copy=False):
        b = self._buf
        b[0] = 0x26
        b[1] = (int(bool(enable_reverse_in_copy))<<4)|int(bool(enable_fill))
        self.command(b, 2)

    def scrolling(self,
                  n_column_hscroll_offset,
                  start_row,
                  n_row_scrolled,
                  n_row_vscroll_offset,
                  interval):
        b = self._buf
        b[0] = 0x27
        b[1] = n_column_hscroll_offset
        b[2] = start_row
        b[3] = n_row_scrolled
        b[4] = n_row_vscroll_offset
        b[5] = interval
        self.command(b, 6)

    def deactivate_scroll(self):
        b = self._buf
        b[0] = 0x2E
        self.command(b, 1)

    def activate_scroll(self):
        b = self._buf
        b[0] = 0x2F
        self.command(b, 1)

    # convenience functions

    def color_256(self):
        self.set_remap_and_color_depth(color_format=0)

    def color_65k(self):
        self.set_remap_and_color_depth(color_format=1)

def vspi(pinnum_dc=None, pinnum_rst=None, pinnum_cs=None):
    sck_hz = 6*1000*1000			# 6MHz
    if pinnum_dc is None:
        pinnum_dc = config.pin_dc
    if pinnum_rst is None:
        pinnum_rst = config.pin_rst
    if pinnum_cs is None:
        pinnum_cs = config.pin_cs
    vspi = spi.SPI(spi.ID_VSPI, polarity=1, phase=1,
                   bits=8, baudrate=sck_hz)
    disp = SSD1331(spi=vspi,
                   pinnum_cs=pinnum_cs,		# Chip Select
                   pinnum_dc=pinnum_dc,		# Data/Command
                   pinnum_rst=pinnum_rst)	# Reset
    disp.init()
    return disp


#----------------------------------------------------------------------------
#                              display adaptor
#----------------------------------------------------------------------------

class Adaptor(AdaptorBase):

    def __new__(cls, driver, fcf=False, gcf=False):
        if sys.implementation.name == 'micropython':
            # Whene super class is not object, super().__new__ seems to be
            # bound method in the MicroPython.
            self = super().__new__(use_fcf=fcf, use_gcf=gcf)
        else:
            self = super().__new__(cls, use_fcf=fcf, use_gcf=gcf)

        self._driver = driver

        # colors
        self.color_black = Color(0, 0, 0)
        self.color_white = Color(*driver.rgb_max)
        self.gcf_fg_color = self.color_white

        # public methods
        self.pixel = driver.pixel
        self.clear = driver.clear
        self.copy = driver.copy

        return self

    @property
    def display_size(self):
        return (self._driver.WIDTH, self._driver.HEIGHT)

    def display_on(self):
        self._driver.set_display_on()

    def display_off(self):
        self._driver.set_display_off()

    def draw_image(self, col, row, img):
        driver = self._driver
        driver.set_column_address(start=col, end=col+img.w-1)
        driver.set_row_address(start=row)
        driver.send_pixels(img.buf, len(img.buf))

    def draw_line(self,
                  col_start, row_start,
                  col_end, row_end,
                  line_color=None):
        if line_color is None:
            line_color = self.line_color
        return self._driver.draw_line(col_start, row_start,
                                      col_end, row_end,
                                      *line_color.rgb)

    def draw_rect(self,
                  col_start, row_start,
                  col_end, row_end,
                  line_color=None,
                  fill_color=None):
        def listing():
            if line_color is None:
                line_color = self.line_color
            for c in line_color.rgb:
                yield c
            if fill_color is None:
                fill_color = self.fill_color
            for c in fill_color.rgb:
                yield c
        return self._driver.draw_rectangle(col_start, row_start,
                                           col_end, row_end,
                                           *listing())

    def fcf_change_color(self, fg_pixel, bg_pixel):
        return self.fcf.change_color(fg_pixel, bg_pixel)

    def fcf_put(self, col, row, chars, spacing=0):
        fcf = self.fcf
        w = fcf.WIDTH + spacing
        h = fcf.HEIGHT
        pixels = fcf.pixels

        driver = self._driver
        set_column_address = driver.set_column_address
        set_row_address = driver.set_row_address
        send_pixels = driver.send_pixels

        for c in chars:
            set_column_address(start=col, end=col+w-1)
            set_row_address(start=row, end=row+h-1)
            send_pixels(*pixels(c))
            col += w
        return col

    def gcf_put(self, col, row, chars, fg_color=None, spacing=0):
        gcf = self.gcf
        w = gcf.WIDTH + spacing

        driver = self._driver
        get_line = gcf.get_line
        draw_line = driver.draw_line

        if self.gcf_bg_color:
            r, g, b = self.gcf_bg_color.rgb
            driver.draw_rectangle(col, row,
                                  col+(w*len(chars))-1, row+gcf.HEIGHT-1,
                                  r, g, b, r, g, b)

        if fg_color:
            r, g, b = fg_color.rgb
        else:
            r, g, b = self.gcf_fg_color.rgb

        for c in chars:
            for c_beg, r_beg, c_end, r_end in get_line(c):
                draw_line(col+c_beg, row+r_beg,
                          col+c_end, row+r_end,
                          r, g, b)
            col += w
        return col
