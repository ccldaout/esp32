import os
import sys
import _thread
import ssd1331
import uipc
import uwifi
import admin


class TextBoard(object):

    def __init__(self, disp, col_beg, row_beg, col_end, row_end, ch_spacing=0, line_spacing=0):
        self._disp = disp
        self._area = (col_beg, row_beg, col_end, row_end)
        self._fw, self._fh = disp.fcf_size
        self._fw += ch_spacing
        self._fh += line_spacing
        self._ch_spacing = ch_spacing
        self._height = self._fh
        self._ncol = (col_end - col_beg + 1 + ch_spacing)//self._fw
        self._nrow = (row_end - row_beg + 1 + line_spacing)//self._fh
        self._ccol = 0
        self._crow = 0
        self._linefeed = False

    def scrollup(self):
        col_beg, row_beg, col_end, row_end = self._area
        self._disp.copy(col_beg, row_beg + self._fh,
                        col_end, row_end,
                        col_beg, row_beg)
        self._disp.clear(col_beg, row_end - self._fh + 1,
                         col_end, row_end)

    def putc(self, c):
        if c == '\n':
            self._linefeed = True
            return
        if self._ccol == self._ncol:
            self._linefeed = True
        if self._linefeed:
            self._linefeed = False
            self._ccol = 0
            self._crow += 1
            if self._crow == self._nrow:
                self.scrollup()
                self._crow -= 1
        col_beg, row_beg, col_end, row_end = self._area
        col = col_beg + self._ccol * self._fw
        row = row_beg + self._crow * self._fh
        self._disp.fcf_put(col, row, c, self._ch_spacing)
        self._ccol += 1

    def putline(self, msg):
        for c in msg:
            self.putc(c)
        self.putc('\n')
        
class WifiProgressSSD1331(uwifi.WifiProgressBase):

    def __init__(self):
        driver = ssd1331.vspi()
        driver.color_65k()
        driver.set_remap_and_color_depth(column_reverse_order=True,
                                         scan_reverse_on_COM=True)
        driver.enable_fill()
        disp = ssd1331.Adaptor(driver, fcf=True, gcf=True)

        self._top_bg = disp.Color(0, 0, 5)
        self._mode_bg1 = disp.Color(31, 0, 0) 
        self._mode_bg2 = disp.Color(0, 54, 0)
        self._ssid_fg1 = disp.Color(25, 50, 0)
        self._ssid_fg2 = disp.Color(0, 54, 0)
        self._ip_fg1 = disp.color_white

        self._mode = None
        self._message = ['' for _ in range(5)]
        self._ssid = None

        self._text = TextBoard(disp, 0, 26, 95, 63)

        self._disp = disp
        self._disp_init()

    def _disp_init(self):
        d = self._disp
        d.clear()
        w, _ = d.display_size
        d.draw_rect(0, 0, w-1, 23, self._top_bg, self._top_bg)

    def _disp_mode(self, mode, fix):
        d = self._disp
        fg = self._top_bg
        bg = self._mode_bg2 if fix else self._mode_bg1
        d.draw_rect(2, 1, 15, 11, bg, bg)
        d.gcf_put(3, 2, mode, fg)

    def _disp_ssid(self, ssid, fix):
        d = self._disp
        fg = self._ssid_fg2 if fix else self._ssid_fg1
        d.draw_rect(19, 2, 93, 11, self._top_bg, self._top_bg)
        d.gcf_put(19, 2, ssid, fg, spacing=1)

    def _disp_ip(self, ip_address):
        d = self._disp
        d.draw_rect(1, 13, 95, 22, self._top_bg, self._top_bg)
        d.gcf_put(2, 13, ip_address, self._ip_fg1, spacing=1)

    def _disp_message(self, msg):
        self._text.putline(msg)

    def init_station_mode(self):
        self._mode = 'ST'

    def init_ap_mode(self):
        self._mode = 'AP'

    def actived(self):
        self._disp_mode(self._mode, False)

    def scanning(self):		# STA mode
        self._disp_message('Scanning ...')

    def connecting(self, ssid):	# STA mode
        self._ssid = ssid
        self._disp_ssid(ssid, False)
        self._disp_message('Connecting ...')

    def ip_address(self, ip_address):
        self._disp_ssid(self._ssid, True)
        self._disp_mode(self._mode, True)
        self._disp_ip(ip_address)
        self._disp_message('Ready !!')


def start_wifi():
    wifi = uwifi.WifiNetwork(WifiProgressSSD1331())
    if not wifi.try_station_mode():
        wifi.start_ap_mode()
    if wifi.ip_address:
        uipc.manager.ip_address = wifi.ip_address
        uipc.manager.register_server(2000, admin.AdminService())

_thread.start_new_thread(start_wifi, ())
