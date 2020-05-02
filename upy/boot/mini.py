import os
import network
import socket
import sys
import _thread

def handle_put(sock, path):
    with open(path, 'wb') as f:
        while True:
            data = sock.recv(512)
            if not data:
                return
            f.write(data)

def handle_get(sock, path):
    with open(path, 'rb') as f:
        while True:
            data = f.read(512)
            if not data:
                return
            sock.write(data)

def handle(sock):
    cmd = str(sock.readline().strip(), 'ascii')
    if cmd in ('put', 'get', 'mkdir'):
        path = sock.readline().strip()
        if cmd == 'put':
            handle_put(sock, path)
        elif cmd == 'get':
            handle_get(sock, path)
        elif cmd == 'mkdir':
            os.mkdir(path)

def server():
    wifi = network.WLAN(network.AP_IF)
    wifi.active(True)
    wifi.config(essid='esp32')
    ip_address = wifi.ifconfig()[0]

    svrsock = socket.socket()
    svrsock.bind((ip_address, 3000))
    svrsock.listen(1)

    while True:
        sock, _ = svrsock.accept()
        try:
            handle(sock)
        except Exception as e:
            sys.print_exception(e)
        finally:
            try:
                sock.close()
            except Exception as e:
                sys.print_exception(e)

def start(*args, **kws):
    _thread.start_new_thread(server, ())
