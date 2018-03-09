import os
import time
import _thread

BOOT_MODE_DIR = ['/', '/BOOT.MINI', '/BOOT.FULL']
BOOT_MODE = 0

def enable_bootmode(sleep_s, mode):
    time.sleep(sleep_s)
    os.mkdir(BOOT_MODE_DIR[mode])

for m, d in enumerate(BOOT_MODE_DIR):
    try:
        os.stat(d)
        BOOT_MODE = m
    except:
        pass

if BOOT_MODE == 2:
    try:
        os.rmdir(BOOT_MODE_DIR[BOOT_MODE])
    except:
        pass
    import boot.full
    _thread.start_new_thread(enable_bootmode, (10, BOOT_MODE))

elif BOOT_MODE == 1:
    try:
        os.rmdir(BOOT_MODE_DIR[BOOT_MODE])
    except:
        pass
    import boot.mini
    _thread.start_new_thread(enable_bootmode, (10, BOOT_MODE))

else:
    for d in BOOT_MODE_DIR:
        try:
            os.mkdir(d)
        except:
            pass
