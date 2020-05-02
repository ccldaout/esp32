def _boot():
    import os
    import machine
    import sys

    try:
        BOOT_PIN = 2
        BOOT_MODE = 0

        value = machine.Pin(BOOT_PIN, machine.Pin.IN).value()

        print('boot: PIN#%d: %d' % (BOOT_PIN, value))

        if value == 0:
            print('boot: full mode ...')
            from boot.full import start
            try:
                from main import main
            except:
                main = None
            start(main)

        else:
            import time
            for i in range(5):
                print('boot: wait for interrupt', '.'*(i+1), end='\r')
                time.sleep(1)
            print()
            print('boot: mini mode ...')
            from boot.mini import start
            start()

        def cat(path):
            with open(path) as f:
                for s in f:
                    print(s.rstrip())

        def rmmod(modname):
            del sys.modules[modname]

        gdic = globals()
        gdic['cd'] = os.chdir
        gdic['ls'] = os.listdir
        gdic['cat'] = cat
        gdic['rmmod'] = rmmod

    except Exception as e:
        sys.print_exception(e)

_boot()
del _boot

