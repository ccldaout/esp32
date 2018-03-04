# coding: utf-8

import ui

class MessageDialog(object):
	def __init__(self):
		self.view = ui.load_view('mdialog')
		self.textview = self.view['message_view']
		self.ok_button = self.view['ok_button']
		self.ok_button.action = self.close
		
	def open(self):
		self.textview.text = ''
		self.view.present('popover')
	
	def close(self, sender=None):
		self.view.close()

	def put(self, message):
		self.textview.text += message

