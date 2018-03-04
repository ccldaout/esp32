import os
import sys
import _thread
import ssd1331
import uipc
import uwifi
import admin


DISP_W = 96
DISP_H = 64


class WifiProgressSSD1331(uwifi.WifiProgressBase):

    def __init__(self):
        driver = ssd1331.vspi()
        driver.color_65k()
        driver.set_remap_and_color_depth(column_reverse_order=True,
                                         scan_reverse_on_COM=True)
        driver.enable_fill()
        disp = ssd1331.Adaptor(driver, fcf=True, gcf=True)

        self._top_bg = disp.Color(0, 0, 1)
        self._mode_bg1 = disp.Color(31, 0, 0) 
        self._mode_bg2 = disp.Color(0, 54, 0)
        self._ssid_fg1 = disp.Color(25, 50, 0)
        self._ssid_fg2 = disp.Color(0, 54, 0)
        self._ip_fg1 = disp.color_white

        self._mode = None
        self._message = ['', '']
        self._ssid = None

        self._disp = disp
        self._disp_init()

    def _disp_init(self):
        d = self._disp
        d.clear()
        d.draw_rect(0, 0, DISP_W-1, 34, self._top_bg, self._top_bg)
        for x in (27, 49, 71):
            d.draw_rect(x, 28, x+1, 29, self._ip_fg1, self._ip_fg1)

    def _disp_mode(self, mode, fix):
        d = self._disp
        fg = self._top_bg
        bg = self._mode_bg2 if fix else self._mode_bg1
        d.draw_rect(3, 2, 16, 16, bg, bg)
        d.gcf_put(4, 3, mode, fg)

    def _disp_ssid(self, ssid, fix):
        d = self._disp
        fg = self._ssid_fg2 if fix else self._ssid_fg1
        d.draw_rect(20, 3, 92, 16, self._top_bg, self._top_bg)
        d.gcf_put(21, 4, ssid, d.color_black)
        d.gcf_put(20, 3, ssid, fg)

    def _disp_ip(self, ip_address):
        d = self._disp
        w = 8
        h = 19
        for s in ['%3s' % s for s in ip_address.split('.')]:
            d.gcf_put(w+1, h+1, s, d.color_black)
            d.gcf_put(w, h, s, self._ip_fg1)
            w += 22

    def _disp_message(self, msg):
        self._message[0] = self._message[1]
        self._message[1] = msg[:15]
        d = self._disp
        d.clear(0, 35, DISP_W-1, 62)
        d.fcf_put(3, 36, self._message[0])
        d.fcf_put(3, 50, self._message[1])

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
