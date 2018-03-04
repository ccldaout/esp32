#!/usr/bin/python2

import binascii
import os
import sys
from tpp import ipc

IP_ADDRESS = os.getenv('ESP32_ADDR', '192.168.0.105')

if len(sys.argv) == 1:
    print 'Usage: espadm put[small] PATH ...'
    print '       espadm mkdir DIR ...'
    print '       espadm reset'
    exit()

def show_result(f):
    def _f(self, path):
        ret = f(self, path)
        print path, '...', ret
        return ret
    return _f

class AdminCommand(object):

    def __init__(self):
        self.cli = None
        self.on_close = None

    def start(self, ip_address):
        self.cli = ipc.SimpleClient((ip_address, 2000), ipc.JSONPacker())
        self.cli.start()

    def stop(self):
        self.cli.close()
        if self.on_close:
            self.on_cloase()

    def _send(self, msg):
        self.cli.send(msg)
        return self.cli.recv()[0] == 'success'

    @show_result
    def put_small(self, path):
        with open(path, 'rb') as f:
            data = binascii.hexlify(f.read())
            return self._send(['put', path, data])

    @show_result
    def put(self, path):
        with open(path, 'rb') as f:
            if not self._send(['put_beg', path]):
                return False
            while True:
                data = f.read(2048)
                if not data:
                    break
                data = binascii.hexlify(data)
                if not self._send(['put_data', data]):
                    return False
            return self._send(['put_end', data])

    @show_result
    def mkdir(self, path):
        return self._send(['mkdir', path])

    def reset(self):
        self.cli.send(['reset'])
        self.stop()

admin = AdminCommand()
admin.start(IP_ADDRESS)

if sys.argv[1] == 'reset':
    admin.reset()

elif sys.argv[1] == 'put':
    for path in sys.argv[2:]:
        admin.put(path)

elif sys.argv[1] == 'putsmall':
    for path in sys.argv[2:]:
        admin.put_small(path)

elif sys.argv[1] == 'mkdir':
    for path in sys.argv[2:]:
        admin.mkdir(path)
