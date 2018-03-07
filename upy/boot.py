NOBOOT = '/NO_BOOT'

import os
try:
    os.stat(NOBOOT)
except:
    os.mkdir(NOBOOT)
    import _thread
    import time
    import boot.wifi
    def enable_bootuser():
        time.sleep(30)
        os.rmdir(NOBOOT)
        print()
    _thread.start_new_thread(enable_bootuser, ())
