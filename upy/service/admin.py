import binascii
import os
import _thread
import machine
import uipc


@uipc.autoreply
class AdminService(uipc.ServiceBase):

    def __init__(self):
        from display import text_board
        self._logger = text_board.putline

    def reset(self, port, msg):
        machine.reset()

    @uipc.autoreply
    def put(self, path, data):
        data = binascii.unhexlify(data)
        with open(path, 'wb') as f:
            f.write(data)
        print(path, '... updated.')

    @uipc.autoreply
    def put_beg(self, path):
        self._path = path
        self._fobj = open(self._path, 'wb')
        print('put', self._path, 'begin')

    @uipc.autoreply
    def put_data(self, data):
        data = binascii.unhexlify(data)
        self._fobj.write(data)
        print('put', self._path, 'data')

    @uipc.autoreply
    def put_end(self):
        self._fobj.close()
        print('put', self._path, 'end')
        self._logger('%s ... OK' % self._path)
        self._fobj = None
        self._path = None

    @uipc.autoreply
    def mkdir(self, path):
        os.mkdir(path)
        self._logger('%s ... OK' % path)

    @uipc.autoreply
    def service(self, modname, portnum):
        svc = __import__('service.' + modname)
        m = getattr(svc, modname)
        f = getattr(m, 'register')
        f(portnum)
        self._logger('%s ... registered' % modname)

    @uipc.autoreply
    def demo(self, modname, args, kwargs):
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
