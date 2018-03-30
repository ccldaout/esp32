#!/bin/python
# -*- coding: utf-8 -*-

import functools
import os
import stat
import sys
import time
from tpp import mipc
from tpp import toolbox as tb
from tpp import threadutil as tu

if os.getenv('DEBUG'):
    def debug(f):
        @functools.wraps(f)
        def _f(*args, **kwargs):
            print f.__name__, args, kwargs, '...'
            r = f(*args, **kwargs)
            print f.__name__, '->', r
            return r
        return _f
else:
    def debug(f):
        return f

class VSRfsService(mipc.ServiceBase):

    def __init__(self, root_dir):
        self._root = os.path.abspath(os.path.expanduser(root_dir))
        self._root_len = len(self._root)
        if not os.path.isdir(self._root):
            raise Exception('%s is not directory.' % root_dir)
        self._obj_lock = tu.Lock()
        self._objs = {}
        self._oh = tb.Counter()

    def _fullpath(self, in_path):
        if in_path[0] == '/':
            return os.path.abspath(self._root + in_path)
        else:
            return os.path.abspath(self._root + os.path.sep + in_path)

    @mipc.autoreply
    @debug
    def check_chdir(self, in_path):
        path = self._fullpath(in_path)
        if os.path.isdir(path):
            return path[self._root_len:]
        raise Exception('%s is not directory.' % in_path)

    @mipc.autoreply
    @debug
    def ilistdir(self, in_path):
        oh = self._oh()
        path = self._fullpath(in_path)
        it = iter(os.listdir(path))
        with self._obj_lock:
            self._objs[oh] = (path, it)
        return oh

    @mipc.autoreply
    @debug
    def ilistdir_next(self, oh):
        with self._obj_lock:
            path, it = self._objs[oh]
        try:
            f = it.next()
        except StopIteration:
            del self._objs[oh]
            return None
        except:
            del self._objs[oh]
            raise
        s = os.stat(path + os.sep + f)
        if stat.S_ISREG(s.st_mode):
            mode = 0x8000
        elif stat.S_ISDIR(s.st_mode):
            mode = 0x4000
        else:
            mode = 0
        return (f, mode, s.st_ino, s.st_size)

    @mipc.autoreply
    @debug
    def mkdir(self, in_path):
        path = self._fullpath(in_path)
        os.mkdir(path)

    @mipc.autoreply
    @debug
    def remove(self, in_path):
        path = self._fullpath(in_path)
        os.remove(path)

    @mipc.autoreply
    @debug
    def rename(self, in_path1, in_path2):
        path1 = self._fullpath(in_path1)
        path2 = self._fullpath(in_path2)
        os.rename(path1, path2)

    @mipc.autoreply
    @debug
    def rmdir(self, in_path):
        path = self._fullpath(in_path)
        os.rmdir(path)

    @mipc.autoreply
    @debug
    def stat(self, in_path):
        path = self._fullpath(in_path)
        try:
            s = os.stat(path)
        except OSError as e:
            return (0,)*10 
        if stat.S_ISREG(s.st_mode):
            mode = 0x8000
        elif stat.S_ISDIR(s.st_mode):
            mode = 0x4000
        else:
            mode = 0
        return (mode, s.st_ino, s.st_dev, s.st_nlink, s.st_uid, s.st_gid,
                s.st_size, s.st_atime, s.st_mtime, s.st_ctime)

    @mipc.autoreply
    @debug
    def statvfs(self, in_path):
        path = self._fullpath(in_path)
        s = os.statvfs(path)
        return (s.f_bsize, s.f_frsize, s.f_blocks, s.f_bfree, s.f_bavail,
                s.f_files, s.f_ffree, s.f_favail, s.f_flag, s.f_namemax)

    @mipc.autoreply
    @debug
    def f_open(self, in_path, mode='r'):
        path = self._fullpath(in_path)
        fobj = open(path, mode)
        oh = self._oh()
        with self._obj_lock:
            self._objs[oh] = fobj
        return (oh, path[self._root_len:])

    @mipc.autoreply
    @debug
    def f_read(self, oh, pos, size):
        with self._obj_lock:
            if oh not in self._objs:
                return (None, None)
            f = self._objs[oh]
        f.seek(pos)
        data = f.read(size)
        pos = f.tell()
        return (pos, data)

    @mipc.autoreply
    @debug
    def f_readline(self, oh, pos, size):
        with self._obj_lock:
            if oh not in self._objs:
                return (None, None)
            f = self._objs[oh]
        f.seek(pos)
        data = f.readline()
        pos = f.tell()
        return (pos, data)

    @mipc.autoreply
    @debug
    def f_write(self, oh, pos, data):
        with self._obj_lock:
            if oh not in self._objs:
                return None
            f = self._objs[oh]
        f.seek(pos)
        n = f.write(data)
        pos = f.tell()
        return (pos, n)

    @mipc.autoreply
    @debug
    def f_seek(self, oh, offset, whence=os.SEEK_SET):
        with self._obj_lock:
            if oh not in self._objs:
                return None
            f = self._objs[oh]
        f.seek(offset, whence)
        pos = f.tell()
        return pos

    @mipc.autoreply
    @debug
    def f_flush(self, oh):
        with self._obj_lock:
            if oh not in self._objs:
                return None
            f = self._objs[oh]
        f.flush()
        pos = f.tell()
        return pos

    @mipc.autoreply
    @debug
    def f_close(self, oh):
        with self._obj_lock:
            if oh not in self._objs:
                return None
            f = self._objs[oh]
            del self._objs[oh]
            f.close()

def main(addr, root_dir, foreground=True):
    port = mipc.udp_server(addr)
    mipc.manager.register(port, VSRfsService(root_dir))
    if foreground:
        time.sleep(-1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print 'Usage: vsrfsd [host]:port root_dir'
        exit(1)
    host, port = sys.argv[1].split(':')
    root_dir = sys.argv[2]
    if not os.path.isdir(root_dir):
        raise TypeError('%s is not directory.' % root_dir)
    main((host, int(port)), root_dir)
