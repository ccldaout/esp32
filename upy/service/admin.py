import binascii
import os
import _thread
import machine

import uipc
from config.service_admin import config


@uipc.autoreply
class AdminService(uipc.ServiceBase):

    def __init__(self):
        from display import text_board
        self._logger = text_board.putline

    def reset(self, port, msg):
        import boot.ena
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
    def get_beg(self, path):
        self._path = path
        self._fobj = open(self._path, 'rb')
        print('get', self._path, 'begin')

    @uipc.autoreply
    def get_data(self):
        data = self._fobj.read(2048)
        if data:
            data = binascii.hexlify(data)
        else:
            self._fobj.close()
            self._fobj = None
            self._path = None
        print('get', self._path, 'data')
        return data

    @uipc.autoreply
    def mkdir(self, path):
        os.mkdir(path)
        self._logger('mkdir %s' % path)

    @uipc.autoreply
    def rmdir(self, path):
        os.rmdir(path)
        self._logger('rmdir %s' % path)

    @uipc.autoreply
    def ls(self, path):
        lis = os.listdir(path)
        self._logger('ls %s' % path)
        return lis

    @uipc.autoreply
    def remove(self, path):
        os.remove(path)
        self._logger('remove %s' % path)

    @uipc.autoreply
    def rename(self, path, path2):
        os.rename(path, path2)
        self._logger('remove %s' % path)

    @uipc.autoreply
    def service(self, modname):
        svc = __import__('service.' + modname)
        m = getattr(svc, modname)
        f = getattr(m, 'register')
        portnum = f()
        self._logger('%s ... registered' % modname)
        return portnum

def register():
    uipc.manager.register_server(config.port, AdminService())
    return config.port
