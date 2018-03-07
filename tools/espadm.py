#!/usr/bin/python2

import binascii
import os
import sys
from tpp import uipc

IP_ADDRESS = os.getenv('ESP32_ADDR', '192.168.0.105')

if len(sys.argv) == 1:
    print 'Usage: espadm put[small] PATH ...'
    print '       espadm mkdir DIR ...'
    print '       espadm reset'
    exit()

class AdminCommand(object):

    def __init__(self):
        self.cli = None
        self.on_close = None

    def start(self, ip_address):
        self.cli = uipc.client((ip_address, 2000))

    def stop(self):
        self.cli.close()
        if self.on_close:
            self.on_cloase()

    def put_small(self, path):
        with open(path, 'rb') as f:
            data = binascii.hexlify(f.read())
            self.cli.put(path, data)

    def put(self, path):
        with open(path, 'rb') as f:
            self.cli.put_beg(path)
            while True:
                data = f.read(2048)
                if not data:
                    break
                data = binascii.hexlify(data)
                self.cli.put_data(data)
            self.cli.put_end()

    def mkdir(self, path):
        self.cli.mkdir(path)

    def service(self, modname, portnum):
        self.cli.service(modname, portnum)

    def reset(self):
        self.cli.reset()
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

elif sys.argv[1] == 'service':
    admin.service(sys.argv[2], int(sys.argv[3]))
