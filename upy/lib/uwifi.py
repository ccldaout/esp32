import network
import time
import _thread


class WifiProgressBase(object):
    def init_ap_mode(self):
        pass
    def init_station_mode(self):
        pass
    def actived(self):
        pass
    def scanning(self):		# STA mode
        pass
    def connecting(self, ssid):	# STA mode
        pass
    def ip_address(self, ip_address):
        print('IP address:', ip_address)

class WifiNetwork(object):
    SCAN_TIMEOUT_s = 10
    SCAN_WAIT_1_s = 0.1
    SCAN_WAIT_n_s = 0.05

    def __init__(self, progress_logger=WifiProgressBase()):
        self._progress = progress_logger
        self.ip_address = ''
        self._init_known_aps()

    def _init_known_aps(self):
        self._known_aps = []
        try:
            with open('data/ssid.lis') as f:
                for s in f:
                    s = s.strip().split('\t')
                    if len(s) == 2:
                        ssid, pwd = s
                        #ssid = bytes((ord(c) for c in ssid))
                        self._known_aps.append((ssid, pwd))
        except:
            pass

    def _try_connect_ap(self, wifi, ssid, pwd):
        self._progress.connecting(ssid)
        wifi.connect(ssid, pwd)
        for _ in range(100):
            time.sleep_ms(50)
            if wifi.isconnected():
                return True
        return False

    def _scan_ap(self, wifi):
        time.sleep(self.SCAN_WAIT_1_s)
        tv = time.time()
        tvlim = tv + self.SCAN_TIMEOUT_s
        self._progress.scanning()
        while tv < tvlim:
            foundaps = set(str(ap[0], 'ascii') for ap in wifi.scan())
            for ssid, pwd in self._known_aps:
                if ssid in foundaps:
                    if self._try_connect_ap(wifi, ssid, pwd):
                        return True
            time.sleep(self.SCAN_WAIT_n_s)
            tv = time.time()
        return False

    def try_station_mode(self):
        if not self._known_aps:
            return False
        wifi = network.WLAN(network.STA_IF)
        self._progress.init_station_mode()
        wifi.active(True)
        self._progress.actived()
        if self._scan_ap(wifi):
            self.ip_address = wifi.ifconfig()[0]
            self._progress.ip_address(self.ip_address)
            return True
        return False

    def start_ap_mode(self):
        wifi = network.WLAN(network.AP_IF)
        self._progress.init_ap_mode()
        wifi.active(True)
        self._progress.actived()
        self.ip_address = wifi.ifconfig()[0]
        self._progress.ip_address(self.ip_address)
