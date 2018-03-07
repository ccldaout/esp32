import json
import socket
import select
import struct
import sys


#----------------------------------------------------------------------------
#
#----------------------------------------------------------------------------

#### thread
import _thread

def _thread_start(func, args, **kwargs):
    return _thread.start_new_thread(func, args)

def _thread_getlock():
    return _thread.allocate_lock()

#### poll
_POLL_IN = select.POLLIN

def _poll_create():
    return select.poll()

def _poll_poller(pollobj):
    return pollobj.ipoll

#### socket.read
def _recvall(sock, n):
    return sock.read(n)
        

#----------------------------------------------------------------------------
#
#----------------------------------------------------------------------------

class PortError(Exception):
    pass

class SocketClosedByPeer(PortError):
    pass

class SocketIOError(PortError):
    pass

class ProtocolError(PortError):
    pass

class RemoteHandlerError(PortError):
    pass

class PackerBase(object):
    def pack(self, msg):
        raise NotImplementedError()
    def unpack(self, sock):
        raise NotImplementedError()
    def __call__(self):
        return self

class DumpPackerBase(object):
    @staticmethod
    def dumps(msg):
        raise NotImplementedError()

    @staticmethod
    def loads(data):
        raise NotImplementedError()

    def pack(self, msg):
        data = self.dumps(msg)
        n = len(data)
        return struct.pack('<i', n)+data, n+4

    def unpack(self, sock):
        size_str = _recvall(sock, 4)
        if len(size_str) != 4:
            raise SocketClosedByPeer()
        n, = struct.unpack('<i', size_str)
        data = _recvall(sock, n)
        if len(data) != n:
            raise SocketClosedByPeer()
        return self.loads(data)

try:
    import cPickle
    class PyPacker(DumpPackerBase):
        dumps = staticmethod(lambda msg: cPickle.dumps(msg, cPickle.HIGHEST_PROTOCOL))
        loads = staticmethod(cPickle.loads)
except:
    pass

class JSONPacker(DumpPackerBase):
    dumps = staticmethod(json.dumps)
    loads = staticmethod(json.loads)


#----------------------------------------------------------------------------
#
#----------------------------------------------------------------------------

class IOPort(object):
    acceptable = False

    def __init__(self, sock=None, packer=None):
        if packer is None:
            packer = JSONPacker()
        if sock:
            self.socket = sock
        self._packer = packer
        self._lock = _thread_getlock()
        self._event = None
        self._autoreply_names = set()

    def connect(self, addr):
        sock = socket.socket()
        sock.connect(addr)
        self.socket = sock
        return self				# for method chain

    def negotiate(self):
        self._autoreply_names = set(self.send(['on_negotiate']).result())
        return self				# for method chain

    def recv(self):
        return self._packer.unpack(self.socket)

    def send(self, msg):
        self._event = msg[0]
        data, n = self._packer.pack(msg)
        with self._lock:
            self.socket.sendall(data)		# raise exception if error
        return self

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

    def result(self):
        ev, status, value = self.recv()
        expect = self._event + '_reply'
        if ev != expect:
            raise ProtocolError('%s is expected, but %s is received.' % (expect, ev))
        if status:
            return value
        raise RemoteHandlerError('Exception happen on remote:\n' + value)

    def __getattr__(self, name):
        def _send(*args):
            msg = [name]
            msg.extend(args)
            self.send(msg)
            if name in self._autoreply_names:
                return self.result()
            return self		# for method chain
        return _send

def client(addr, packer=None):
    return IOPort(packer).connect(addr).negotiate()

class AcceptablePort(object):
    acceptable = True

    def __init__(self, sock_addr):
        self.socket = socket.socket()
        self.socket.bind(sock_addr)
        self.socket.listen(1)

    def accept(self):
        iosocket, _ = self.socket.accept()
        return IOPort(iosocket)

    def close(self):
        if self.socket:
            self.socket.close()
            self.socket = None

class _AutoReply(object):
    def __init__(self):
        self._autoreply_names = set()

    def __contains__(self, item):
        return item in self._autoreply

    def decorator_autoreply(self, target):
        if isinstance(target, type):
            self._autoreply_names.update(target._autoreply_names)
            target._autoreply_names = self._autoreply_names
            self._autoreply_names = set()
            return target
        else:
            target = target
            def wrapper(svc_self, port, msg):	# args: self, port, msg
                reply = msg[0] + '_reply'
                try:
                    ret = target(svc_self, *msg[1:])
                    port.send([reply, True, ret])
                except Exception as e:
                    port.send([reply, False, str(e)])
            self._autoreply_names.add(target.__name__)
            return wrapper

    def decorator_noreply(self, target):
        def wrapper(svc_self, port, msg):	# args: self, port, msg
            ret = target(svc_self, *msg[1:])
        return wrapper

_AutoReply = _AutoReply()
autoreply =_AutoReply.decorator_autoreply
noreply = _AutoReply.decorator_noreply

######## MicroPython don't support metaclasses. ###
####class _ServiceMeta(type):
####    def __new__(mcls, name, bases, dic):
####        cls = super(_ServiceMeta, mcls).__new__(mcls, name, bases, dic)
####        cls = _AutoReply.class_decorator(cls)
####        return cls

class ServiceBase(object):
    ####__metaclass__ = _ServiceMeta

    _autoreply_names = set()

    def __call__(self, port):
        return self

    def on_accepted(self, port):
        pass

    def on_disconnected(self, port):
        pass

    def on_exception(self, port):
        pass

    def on_negotiate(self, port, msg):
        port.send(['on_negotiate_reply', True, list(self._autoreply_names)])

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
        self._poll = _poll_create()
        self._ports = {}
        self.ip_address = None
        _thread_start(self.loop, ())

    def register_server(self, addr, service_object):
        if isinstance(addr, int):
            addr = (self.ip_address, addr)
        port = AcceptablePort(addr)
        self.register(port, service_object)

    def register(self, port, service_object):
        fd = port.socket.fileno()
        self._poll.register(port.socket, _POLL_IN)	# MicroPython
        self._ports[fd] = (port, service_object)

    def unregister(self, port):
        fd = port.socket.fileno()
        self._poll.unregister(port.socket)		# MicroPython
        if fd in self._ports:
            del self._ports[fd]

    def loop(self):
        poller = _poll_poller(self._poll)
        while True:
            for sensed in poller():
                fd = sensed[0].fileno()			# MicroPython
                port, service_object = self._ports[fd]
                if port.acceptable:
                    newport = None
                    try:
                        newport = port.accept()
                        service_object = service_object(port)
                        self.register(newport, service_object)
                        service_object.on_accepted(newport)
                    except Exception as e:
                        if newport:
                            self.unregister(newport)
                            newport.close()
                else:
                    try:
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
