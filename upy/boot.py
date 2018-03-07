NOBOOT = '/NO_BOOT'
try:
    import os
    if not os.path.exists(NOBOOT):
        os.mkdir(NOBOOT)
        import _thread
        import time
        import boot.wifi
        def enable_bootuser():
            time.sleep(60)
            os.rmdir(NOBOOT)
            print()
        _thread.start_new_thread(enable_bootuser, ())
except:
    pass
