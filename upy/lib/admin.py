import binascii
import os
import machine
import uipc


def autoreply(f):
    def _f(self, port, msg):
        try:
            f(self, port, msg)
            port.success()
        except Exception as e:
            print(msg, '... failed:', e)
            port.failure(str(e))
    return _f

class AdminService(uipc.ServiceBase):

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
        self._fobj = None
        self._path = None

    @autoreply
    def mkdir(self, port, msg):
        _, path = msg
        os.mkdir(path)
