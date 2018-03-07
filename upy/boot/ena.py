import os
NOBOOT = '/NO_BOOT'
try:
    os.rmdir(NOBOOT)
except:
    pass
