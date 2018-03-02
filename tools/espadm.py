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

def put_small(args):
    for path in args:
        with open(path, 'rb') as f:
            data = binascii.hexlify(f.read())
            cli.send(['put', path, data])
            m = cli.recv()
            print path, '...', m[0]

def put(args):
    for path in args:
        with open(path, 'rb') as f:
            cli.send(['put_beg', path])
            if cli.recv()[0] == 'failure':
                continue

            while True:
                data = f.read(2048)
                if not data:
                    break
                data = binascii.hexlify(data)
                cli.send(['put_data', data])
                if cli.recv()[0] == 'failure':
                    continue
                
            cli.send(['put_end', data])
            m = cli.recv()
            print path, '...', m[0]

def mkdir(args):
    for path in args:
        cli.send(['mkdir', path])
        m = cli.recv()
        print path, '...', m[0]

cli = ipc.SimpleClient((IP_ADDRESS, 2000), ipc.JSONPacker())
cli.start()

if sys.argv[1] == 'reset':
    cli.send(['reset'])

elif sys.argv[1] == 'put':
    put(sys.argv[2:])

elif sys.argv[1] == 'putsmall':
    put_small(sys.argv[2:])

elif sys.argv[1] == 'mkdir':
    mkdir(sys.argv[2:])