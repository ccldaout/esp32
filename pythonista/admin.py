# coding: utf-8

import binascii
import ui
import glob
from mdialog import MessageDialog
from utils import Config
from tpp import ipc

CONFIG_PATH = '.admin.config'
config = Config.load(CONFIG_PATH)

PY_DIR = '../upy/'

class AdminCommand(object):

    def __init__(self):
        self.cli = None
        self.on_close = None

    def start(self, ip_address):
        self.cli = ipc.SimpleClient((ip_address, 2000), ipc.JSONPacker())
        self.cli.start()

    def stop(self):
        self.cli.close()
        if self.on_close:
            self.on_cloase()

    def _send(self, msg):
        self.cli.send(msg)
        return self.cli.recv()[0] == 'success'

    def put(self, path):
        with open(PY_DIR+path, 'rb') as f:
            if not self._send(['put_beg', path]):
                return False
            while True:
                data = f.read(2048)
                if not data:
                    break
                data = binascii.hexlify(data)
                if not self._send(['put_data', data]):
                    return False
            return self._send(['put_end', data])

    def mkdir(self, path):
        self._send(['mkdir', path])

    def reset(self):
        self.cli.send(['reset'])
        self.stop()

def list_uploadable():
    n = len(PY_DIR)
    for f in glob.glob(PY_DIR+'*.py') + glob.glob(PY_DIR+'*/*.py'):
        yield f[n:]

class Admin(object):

    def __init__(self, topv, mdiag, admcmd):
        self._admcmd = admcmd
        self._mdiag = mdiag

        topv.background_color = '#2f2f2f'

        v = topv['ip_address']
        v.action = self.enter_ipaddress
        if config.ip_address:
            v.text = config.ip_address

        v = topv['connect']
        v.action = self.do_connect

        v = topv['upload']
        v.action = self.do_upload

        v = topv['clear_selection']
        v.action = self.do_clear_selection

        v = topv['reset']
        v.action = self.do_reset

        self.v_status = topv['ipc_status']

        v = topv['file_selection']
        v.data_source = ui.ListDataSource(list_uploadable())
        v.allows_multiple_selection = True
        self.v_fileselection = v

    def ipc_ready(self, status):
        if status:
            self.v_status.text = 'Ready'
            self.v_status.background_color = '#00f816'
        else:
            self.v_status.text = 'Not Ready'
            self.v_status.background_color = '#aeaeae'

    def enter_ipaddress(self, sender):
        config.ip_address = sender.text
        config.save()

    def do_connect(self, sender):
        self._admcmd.start(config.ip_address)
        self.ipc_ready(True)

    def do_clear_selection(self, sender):
        v = ui.TextView()

        self.v_fileselection.reload()

    def do_upload(self, sender):
        self._mdiag.open()
        files = self.v_fileselection.data_source.items
        for _, row in self.v_fileselection.selected_rows:
            path = files[row]
            ret = self._admcmd.put(path)
            self._mdiag.put('%s ... %s\n' % (path, ('NG', 'OK')[bool(ret)]))
        self.v_fileselection.reload()

    def do_reset(self, sender):
        self._admcmd.reset()
        self.ipc_ready(False)

mainview = ui.load_view()
Admin(mainview, MessageDialog(), AdminCommand())
mainview.present('sheet')

