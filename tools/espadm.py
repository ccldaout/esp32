#!/usr/bin/python2

import binascii
import os
import sys
from tpp import mipc

class AdminCommand(object):

    def __init__(self):
        self.cli = None
        self.on_close = None

    def start(self, ip_address):
        self.cli = mipc.client((ip_address, 2000))

    def stop(self):
        self.cli.close()
        if self.on_close:
            self.on_cloase()

    def reset(self):
        self.cli.reset()
        self.stop()

    def put_small(self, path):
        with open(path, 'rb') as f:
            data = binascii.hexlify(f.read())
            self.cli.put(path, data)

    def put(self, path):
        with open(path, 'rb') as f:
            self.cli.put_beg(path)
            while True:
                data = f.read(1024)
                if not data:
                    break
                data = binascii.hexlify(data)
                self.cli.put_data(data)
            self.cli.put_end()

    def get(self, path):
        with open(path+'.tmp', 'wb') as f:
            self.cli.get_beg(path)
            while True:
                data = self.cli.get_data()
                if not data:
                    break
                data = binascii.unhexlify(data)
                f.write(data)
        if os.path.exists(path):
            os.rename(path, path+'.bck')
        os.rename(path+'.tmp', path)

    def mkdir(self, path):
        self.cli.mkdir(path)

    def rmdir(self, path):
        self.cli.rmdir(path)

    def ls(self, path):
        print path
        print ' ', self.cli.ls(path)

    def remove(self, path):
        self.cli.remove(path)

    def rename(self, source, target):
        self.cli.rename(source, target)

    def display_on(self):
        self.cli.display_on()

    def display_off(self):
        self.cli.display_off()

    def service(self, modname):
        return self.cli.service(modname)

IP_ADDRESS = os.getenv('ESP32_ADDR', '192.168.0.105')

admin = AdminCommand()
admin.start(IP_ADDRESS)

if len(sys.argv) == 1:
    print 'Usage: espadm put[small] PATH ...'
    print '              get PATH ...'
    print '              mkdir DIR ...'
    print '              rmdir DIR ...'
    print '              ls DIR ...'
    print '              remove PATH ...'
    print '              rename OLD NEW'
    print '              service SERVICE'
    print '              display {on|off}'
    print '              reset'
    exit()

if sys.argv[1] == 'reset':
    admin.reset()

elif sys.argv[1] == 'putsmall':
    for path in sys.argv[2:]:
        admin.put_small(path)

elif sys.argv[1] == 'put':
    for path in sys.argv[2:]:
        admin.put(path)

elif sys.argv[1] == 'get':
    for path in sys.argv[2:]:
        admin.get(path)

elif sys.argv[1] == 'mkdir':
    for path in sys.argv[2:]:
        admin.mkdir(path)

elif sys.argv[1] == 'rmdir':
    for path in sys.argv[2:]:
        admin.rmdir(path)
    
elif sys.argv[1] == 'ls':
    for path in sys.argv[2:]:
        admin.ls(path)

elif sys.argv[1] == 'remove':
    for path in sys.argv[2:]:
        admin.remove(path)

elif sys.argv[1] == 'rename':
    admin.rename(sys.argv[2], sys.argv[3])

elif sys.argv[1] == 'display':
    if sys.argv[2] == 'on':
        admin.display_on()
    elif sys.argv[2] == 'off':
        admin.display_off()
    else:
        print 'display require on/off'

elif sys.argv[1] == 'service':
    port = admin.service(sys.argv[2])
    print 'port:', port

else:
    print 'Unknown command:', sys.argv[1]
