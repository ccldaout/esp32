import time
from threading import *

cond = Condition()
perm = [2, 4, 6, 8]

def sub(v):
    print(v, 'started')
    with cond:
        s = cond.wait(5)
        print(v, 'cond.wait', s)
        if not s:
            print(v, 'abort')
            return
        if v in perm:
            print(v, 'success')
            return
        print(v, 'retry')

tid = 0
def t():
    global tid
    n = 3
    for v in range(tid, tid+n):
        t = Thread(target=sub, args=(v,))
        t.start()
    tid += n

def n():
    with cond:
        print('notify')
        cond.notify()

def a():
    with cond:
        print('notify_all')
        cond.notify_all()

t()
time.sleep(0.5)
n()
time.sleep(0.5)
a()
t()
time.sleep(1)
n()
n()
n()
