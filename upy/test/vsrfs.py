import genstream
import mipc
import os

def debug(f):
    def wrapper(*args, **kwargs):
        print(f.__name__, args, kwargs)
        return f(*args, **kwargs)
    return wrapper

_UNIT_SIZE = mipc.UDPDumpPackerBase.MAXLEN // 2
_MAX_SIZE = 2 * 1024 * 1024

class VSRfsFile(genstream.genstream):

    def __init__(self, addr, path, mode):
        self._port = mipc.udp_client(addr)
        oh, abspath = self._port.f_open(path, mode)
        self._pos = 0
        self._oh = oh
        self._abspath = path

    def read(self, size=None):
        def _read_by_unit(size):
            while size > 0:
                r = _UNIT_SIZE if size > _UNIT_SIZE else size
                self._pos, data = self._port.f_read(self._oh, self._pos, r)
                if not data:
                    return
                yield data
                size -= len(data)
        if size is not None and size < _UNIT_SIZE:
            self._pos, data = self._port.f_read(self._oh, self._pos, size)
        else:
            if size is None:
                size = _MAX_SIZE
            data = ''.join(_read_by_unit(size))
        return data

    def readinto(self, buf):
        data = self.read(len(buf))
        n = len(data)
        buf[:n] = data
        return len(data)

    def readline(self, size=-1):
        self._pos, data = self._port.f_readline(self._oh, self._pos, size)
        return data

    def readlines(self, b):
        ls = []
        while True:
            s = self.readline()
            if not s:
                return ls
            ls.append(s)

    def write(self, data):
        size = len(data)
        if size < _UNIT_SIZE:
            self._pos, n = self._port.f_write(self._oh, self._pos, data)
        else:
            n = 0
            while size > 0:
                r = _UNIT_SIZE if size > _UNIT_SIZE else size
                self._pos, r = self._port.f_write(self._oh, self._pos, r)
                size -= r
                n += r
        return n

    def seek(self, offset, whence=0):
        self._pos = self._port.f_seek(self._oh, offset, whence)
        return self._pos

    def tell(self):
        self._pos

    def flush(self):
        self._pos = self._port.f_flush(self._oh)

    def close(self):
        if self._port:
            self._port.f_close(self._oh)
            self._port.close()
            self._port = None

    def __iter__(self):
        while True:
            self._pos, data = self._port.f_readline(self._oh, self._pos, 0)
            if not data:
                return
            yield data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.close()

    def __del__(self):
        self.close()

class VSRfs(object):

    def __init__(self, addr):
        self._addr = addr	# (host, port)
        self._port = None
        self._cwd = '/'

    def _fullpath(self, path):
        if not path:
            return self._cwd
        if path[0] == '/':
            return path
        return self._cwd + '/' + path

    def mount(self, dev, mount_point):
        self._port = mipc.udp_client(self._addr)

    def umount(self):
        self._port.close()
        self._port = None

    def chdir(self, path):
        path = self._fullpath(path)
        self._cwd = self._port.check_chdir(path)

    def getcwd(self):
        return self._cwd

    def ilistdir(self, path):
        port = mipc.udp_client(self._addr)
        oh = self._port.ilistdir(path)
        while True:
            v = port.ilistdir_next(oh)
            if not v:
                return
            yield v

    def mkdir(self, path):
        path = self._fullpath(path)
        self._port.mkdir(path)

    def remove(self, path):
        path = self._fullpath(path)
        self._port.remove(path)

    def rename(self, path1, path2):
        path1 = self._fullpath(path1)
        path2 = self._fullpath(path2)
        self._port.rename(path1, path2)

    def rmdir(self, path):
        path = self._fullpath(path)
        self._port.rmdir(path)

    def stat(self, path):
        path = self._fullpath(path)
        return tuple(self._port.stat(path))

    def statvfs(self, path):
        path = self._fullpath(path)
        return self._port.statvfs(path)

    def open(self, path, mode='r', *args, **kwargs):
        path = self._fullpath(path)
        return VSRfsFile(self._addr, path, mode)

def test():
    import sys
    vsrfs = VSRfs(('192.168.0.107', 2002))
    os.mount(vsrfs, '/V')
    sys.path.append('/V/sub')
    import ttt
