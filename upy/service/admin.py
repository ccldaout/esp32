import binascii
import os
import _thread
import machine
import uipc


def autoreply(f):
    def _f(self, port, msg):
        try:
            ret = f(self, port, msg)
            port.success(ret)
        except Exception as e:
            print(msg, '... failed:', e)
            port.failure(str(e))
    return _f

class AdminService(uipc.ServiceBase):

    def __init__(self):
        from display import text_board
        self._logger = text_board.putline

    def reset(self, port, msg):
        machine.reset()

    @autoreply
    def put(self, port, msg):
        _, path, data = msg
        data = binascii.unhexlify(data)
        with open(path, 'wb') as f:
            f.write(data)
        print(path, '... updated.')

    @autoreply
    def put_beg(self, port, msg):
        _, self._path = msg
        self._fobj = open(self._path, 'wb')
        print('put', self._path, 'begin')

    @autoreply
    def put_data(self, port, msg):
        _, data = msg
        data = binascii.unhexlify(data)
        self._fobj.write(data)
        print('put', self._path, 'data')

    @autoreply
    def put_end(self, port, msg):
        self._fobj.close()
        print('put', self._path, 'end')
        self._logger('%s ... OK' % self._path)
        self._fobj = None
        self._path = None

    @autoreply
    def mkdir(self, port, msg):
        _, path = msg
        os.mkdir(path)
        self._logger('%s ... OK' % path)

    @autoreply
    def service(self, port, msg):
        _, modname, portnum = msg
        svc = __import__('service.' + modname)
        m = getattr(svc, modname)
        f = getattr(m, 'register')
        f(portnum)
        self._logger('%s ... registered' % modname)

    @autoreply
    def demo(self, port, msg):
        _, modname, args, kwargs = msg
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        demo = __import__('demo.' + modname)
        m = getattr(demo, modname)
        f = getattr(m, 'demo')
        _thread.start_new_thread(f, ())


def register(port):
    uipc.manager.register_server(port, AdminService())
