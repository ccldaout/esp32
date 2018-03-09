import os
import network
import socket
import _thread

def handle_put(sock, path):
    with open(path, 'wb') as f:
        while True:
            data = sock.read(512)
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
    cmd = sock.readline().strip()
    if cmd in ('put', 'get', 'mkdir'):
        path = sock.readline().strip()
        if cmd == 'put':
            handle_put(sock, path)
        elif cmd == 'get':
            handle_get(sock, path)
        else cmd == 'mkdir':
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
        sock = svrsock.accept()
        try:
            handle(sock)
        except:
            pass
        finally:
            try:
                sock.close()
            except:
                pass

_thread.start_new_thread(server, ())
