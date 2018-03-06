import json
import socket
import select
import struct
import sys
import _thread


class SocketClosedByPeer(Exception):
    pass

class SocketIOError(Exception):
    pass

class JSONPacker(object):
    def pack(self, msg):
        data = json.dumps(msg)
        n = len(data)
        return (struct.pack('<i', n)+data, n+4)

    def unpack(self, sockobj):
        size_str = sockobj.read(4)
        if len(size_str) != 4:
            raise SocketClosedByPeer()
        n, = struct.unpack('<i', size_str)
        data = sockobj.read(n)
        if len(data) != n:
            raise SocketClosedByPeer()
        return json.loads(data)

    def __call__(self):
        return self

class IOPort(object):
    acceptable = False

    def __init__(self, sockobj, packer=JSONPacker()):
        self.socket = sockobj
        self._packer = packer
        self._lock = _thread.allocate_lock()

    def recv(self):
        return self._packer.unpack(self.socket)

    def send(self, msg):
        data, n = self._packer.pack(msg)
        with self._lock:
            z = self.socket.write(data)
        if n != z:
            raise SocketIOError()
        return z

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def __getattr__(self, name):
        def _send(*args):
            msg = [name]
            msg.extend(args)
            return self.send(msg)
        return _send

class AcceptablePort(object):
    acceptable = True

    def __init__(self, sock_addr):
        self.socket = socket.socket()
        self.socket.bind(sock_addr)
        self.socket.listen(1)

    def accept(self):
        iosocket, _ = self.socket.accept()
        return IOPort(iosocket)

class ServiceBase(object):
    def __call__(self, port):
        return self

    def on_accepted(self, port):
        pass

    def on_disconnected(self, port):
        pass

    def on_exception(self, port):
        pass

    def on_default(self, port, msg):
        raise NotImplementedError(msg[0])

    def on_received(self, port, msg):
        name = msg[0]
        if hasattr(self, name):
            getattr(self, name)(port, msg)
        else:
            self.on_default(port, msg)

class _ServiceManager(object):
    def __init__(self):
        self._poll = select.poll()
        self._ports = {}
        self.ip_address = None
        _thread.start_new_thread(self.loop, ())

    def register_server(self, addr, service_object):
        if isinstance(addr, int):
            addr = (self.ip_address, addr)
        port = AcceptablePort(addr)
        self.register(port, service_object)

    def register(self, port, service_object):
        self._poll.register(port.socket, select.POLLIN)
        self._ports[port.socket.fileno()] = (port, service_object)

    def unregister(self, port):
        self._poll.unregister(port.socket)
        del self._ports[port.socket.fileno()]

    def loop(self):
        while True:
            for sensed in self._poll.ipoll():
                sock = sensed[0]
                port, service_object = self._ports[sock.fileno()]
                try:
                    if port.acceptable:
                        newport = port.accept()
                        service_object = service_object(port)
                        self.register(newport, service_object)
                        service_object.on_accepted(newport)
                    else:
                        msg = port.recv()
                        service_object.on_received(port, msg)
                except SocketClosedByPeer:
                    self.unregister(port)
                    service_object.on_disconnected(port)
                    port.close()
                except:
                    self.unregister(port)
                    service_object.on_exception(port)
                    port.close()

manager = _ServiceManager()
