# coding: utf-8

import binascii
import ui
import glob
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
	def __init__(self, topv, admcmd):
		self._admcmd = admcmd
		
		topv.background_color = '#2f2f2f'
		
		v_ipaddress = topv['ip_address']
		v_ipaddress.action = self.enter_ipaddress
		if config.ip_address:
			v_ipaddress.text = config.ip_address
			
		v_button_connect = topv['connect']
		v_button_connect.action = self.do_connect
		
		v_button_upload = topv['upload']
		v_button_upload.action = self.do_upload
		
		v_button_reset = topv['reset']
		v_button_reset.action = self.do_reset
		
		self.v_status = topv['ipc_status']
		
		v_fileselection = topv['file_selection']
		v_fileselection.data_source = ui.ListDataSource(list_uploadable())
		v_fileselection.allows_multiple_selection = True
		self.v_fileselection = v_fileselection
		
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
		
	def do_upload(self, sender):
		files = self.v_fileselection.data_source.items
		for row, _ in self.v_fileselection.selected_rows:
			self._admcmd.put(files[row])
		self.v_fileselection.reload()
		
	def do_reset(self, sender):
		self._admcmd.reset()
		self.ipc_ready(False)
		
v = ui.load_view()
Admin(v, AdminCommand())
v.present('sheet')

