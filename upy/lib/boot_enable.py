import os
try:
    os.rename('boot.py.disabled',
              'boot.py')
except:
    pass
