# -*- coding: utf-8 -*-

import sys
import time
if sys.implementation.name != 'micropython':
    import traceback
import _thread

get_ident = _thread.get_ident

class _UniqId(object):
    def __init__(self):
        self._threads = {}
        self._uniq_id = 0
        self._lock = _thread.allocate_lock()

    def acquire(self):
        with self._lock:
            self._uniq_id += 1
            id = self._uniq_id
            self._threads[_thread.get_ident()] = id
            return id

    def release(self):
        with self._lock:
            del self._threads[_thread.get_ident()]

    def current(self):
        with self._lock:
            return self._threads[_thread.get_ident()]

_uniq_id = _UniqId()
_uniq_id.acquire()

class Event(object):

    def __init__(self):
        self._semaphore = _thread.allocate_lock()
        self.clear()

    def clear(self):
        self._semaphore.acquire(0)

    def is_set(self):
        return not self._semaphore.locked()

    def set(self):
        try:
            self._semaphore.release()
        except:
            pass

    def wait(self, timeout=None):
        if timeout is None:
            waitflag, timeout = -1, -1
        elif timeout == 0:
            waitflag, timeout = 0, -1
        else:
            waitflag, timeout = -1, timeout
        if self._semaphore.acquire(waitflag, timeout):
            try:
                self._semaphore.release()
            except:
                pass
            return True
        return False

class Lock(object):

    def __init__(self):
        self._lock = _thread.allocate_lock()
        self._i_lock = _thread.allocate_lock()
        self._i_locked_by = None

    def acquire(self, blocking=True, timeout=-1):
        if self._lock.acquire(int(blocking), timeout):
            with self._i_lock:
                self._i_locked_by = _uniq_id.current()
                return True
        return False

    def release(self):
        with self._i_lock:
            self._lock.release()
            self._i_locked_by = None

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.release()

    def locked(self):
        return self._lock.locked()

    def _locked_by_me(self):
        with self._i_lock:
            return (self._i_locked_by == _uniq_id.current())

class RLock(object):

    def __init__(self):
        self._lock = _thread.allocate_lock()
        self._locked_by = None
        self._locked_n = 0

    def acquire(self, blocking=True, timeout=-1):
        if self._locked_by == _uniq_id.current():
            self._locked_n += 1
            return True
        if not self._lock.acquire(int(blocking), timeout):
            return False
        self._locked_n = 1
        self._locked_by = _uniq_id.current()
        return True

    def release(self):
        if not self._locked_by_me():
            raise RuntimeError('lock is not mine')
        self._locked_n -= 1
        if self._locked_n == 0:
            self._locked_by = None
            self._lock.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.release()

    def locked(self):
        return self._lock.locked()

    def _locked_by_me(self):
        return (self._locked_by == _uniq_id.current())

class Condition(object):

    def __init__(self, lock=None):
        self._wakeup_event = Event()
        self._mutex = lock if lock else RLock()
        self._wait_n = 0
        self._id = 0
        self._wakeup_max_id = 0
        self._wakeup_n = 0

    def wait(self, timeout=None):
        if not self._mutex._locked_by_me():
            raise RuntimeError('mutex is not locked')

        self._id += 1
        id = self._id
        self._wait_n += 1

        while True:
            self._mutex.release()
            tv = time.time()

            if not self._wakeup_event.wait(timeout):
                self._mutex.acquire()
                return False

            self._mutex.acquire()
            if id <= self._wakeup_max_id and self._wakeup_n:
                self._wait_n -= 1
                self._wakeup_n -= 1
                if self._wakeup_n:
                    self._wakeup_event.clear()
                return True

            if timeout is not None:
                timeout -= (time.time() - tv)
                if timeout <= 0.0:
                    timeout = 0

    def notify(self):
        if not self._mutex._locked_by_me():
            raise RuntimeError('mutex is not locked')
        if self._wait_n:
            if self._wakeup_n == 0:
                self._wakeup_max_id = self._id
                self._wakeup_n = 1
            else:
                self._wakeup_max_id = self._id
                self._wakeup_n += 1
            self._wakeup_event.set()
                
    def notify_all(self):
        if not self._mutex._locked_by_me():
            raise RuntimeError('mutex is not locked')
        if self._wait_n:
            self._wakeup_max_id = self._id
            self._wakeup_n = self._wait_n
            self._wakeup_event.set()

    def acquire(self, *args):
        return self._mutex.acquire(*args)

    def release(self):
        return self._mutex.release()

    def __enter__(self):
        self.acquire()

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.release()

class Thread(object):
    _g_lock = _thread.allocate_lock()
    _threads = {}

    @classmethod
    def _current_thread(cls):
        return cls._threads[get_ident()]

    @classmethod
    def _enumerate(cls):
        return cls._threads.values()

    def __init__(self, *, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        if not isinstance(args, tuple):
            raise TypeError('args must be tuple')
        if kwargs is not None and not isinstance(kwargs, dict):
            raise TypeError('kwargs must be dict')
        self._target = target
        self._args = args
        self._kwargs = kwargs if kwargs else {}
        self.name = name if name else '' 
        self.ident = None
        self._alive = False
        self._started = False
        self._uniq_id = -1
        self._join_event = Event()

    def _thread(self, target, args, kwargs):
        try:
            with self._g_lock:
                self._alive = True
                self.ident = get_ident()
                self._threads[self.ident] = self
                self._uniq_id = _uniq_id.acquire()
                if not self.name:
                    self.name = 'Thread#%d' % self._uniq_id
            target(*args, **kwargs)
        except Exception as e:
            if sys.implementation.name == 'micropython':
                sys.print_exception(e)
            else:
                traceback.print_exc()
        finally:
            with self._g_lock:
                self._alive = False
            _uniq_id.release()
            del self._threads[self.ident]
            self._join_event.set()

    def __str__(self):
        return ('<%s (%d) started:%s alive:%s>' % (
            self.name, self._uniq_id, self._started, self._alive))

    __repr__ = __str__

    def start(self):
        with self._g_lock:
            if not self._target:
                raise RuntimeError('no target is specified or alread started.')
            self._started = True
            self._join_event.clear()
            _thread.start_new_thread(self._thread, (self._target, self._args, self._kwargs))
            self._target = None

    def join(self, timeout=None):
        with self._g_lock:
            if not self._started:
                raise RuntimeError('Not started yet.')
            if self._uniq_id == _uniq_id.current():
                raise RuntimeError('join self.')
        return self._join_event.wait(timeout)

    def is_alive(self):
        with self._g_lock:
            return self._alive

_main_thread = Thread()
_main_thread.name = 'main'
_main_thread.ident = get_ident()
_main_thread._alive = True
_main_thread._started = True
Thread._threads[_main_thread.ident] = _main_thread

current_thread = Thread._current_thread
enumerate = Thread._enumerate
