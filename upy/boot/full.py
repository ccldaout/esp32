import os
import sys
import _thread
import ssd1331
import machine
import mipc
import wifi
import service

from config.boot_full import config

        
def setup_SSD1331():
    driver = ssd1331.vspi()
    driver.color_65k()
    driver.set_remap_and_color_depth(column_reverse_order=True,
                                     scan_reverse_on_COM=True)
    driver.enable_fill()
    return ssd1331.Adaptor(driver, fcf=True, gcf=True)
    

class WifiProgressSSD1331(wifi.WifiProgressBase):

    def __init__(self, disp):
        self._top_bg = disp.Color(0, 0, 2)
        self._mode_bg1 = disp.Color(31, 0, 0) 
        self._mode_bg2 = disp.Color(0, 54, 0)
        self._ssid_fg1 = disp.Color(25, 50, 0)
        self._ssid_fg2 = disp.Color(0, 54, 0)
        self._ip_fg1 = disp.color_white

        self._mode = None
        self._message = ['' for _ in range(5)]
        self._ssid = None

        self._text = ssd1331.TextBoard(disp, 0, 26, 95, 63)

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
        d = self._disp
        d.draw_rect(19, 2, 93, 11, self._top_bg, self._top_bg)
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


def setup_Wifi(disp_ssd1331=None):
    progress = wifi.WifiProgressBase()
    if config.progress_ssd1331 and disp_ssd1331:
        try:
            progress = WifiProgressSSD1331(disp_ssd1331)
        except:
            pass

    wlan = wifi.WifiNetwork(progress)
    if not wlan.try_station_mode():
        wlan.start_ap_mode()
    if wlan.ip_address:
        for svcname in config.services:
            svcmod = __import__('service.'+svcname)
            mod = getattr(svcmod, svcname)
            register = getattr(mod, 'register')
            register()
    

def _start(main_func=None):
    disp_ssd1331 = setup_SSD1331() if config.ssd1331 else None

    if config.enable_wifi_pin is not None:
        p = machine.Pin(config.enable_wifi_pin, machine.Pin.IN)
        if p.value() == 0:
            setup_Wifi(disp_ssd1331)

    if main_func:
        main_func()


def start(main=None, *args, **kws):
    _thread.start_new_thread(_start, (main,))
