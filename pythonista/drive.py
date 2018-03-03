# coding: utf-8

import ui
from tpp import ipc

class ControlPad(ui.View):
	def __init__(self):
		self.vector = lambda x,y:None
		self.center_x = 150.0 #self.bounds[2]/2
		self.center_y = 150.0 #self.bounds[3]/2
		self.half_width = self.center_x
		self.move_threashold = 0.005
		self.set_needs_display()
		
	def draw(self):
		path = ui.Path()
		path.line_width = 1
		path.line_join_style = ui.LINE_JOIN_ROUND
		path.line_cap_style = ui.LINE_CAP_ROUND
		path.move_to(self.center_x, 0)
		path.line_to(self.center_x, self.center_y*2)
		path.stroke()
		path.move_to(0, self.center_y)
		path.line_to(self.center_x*2, self.center_y)
		path.stroke()
		
	def touch_began(self, touch):
		x, y = touch.location
		self.xy = ((x - self.center_x)/self.half_width,
		(self.center_y - y)/self.half_width)
		self.vector(self.xy)
		
	def touch_moved(self, touch):
		x, y = touch.location
		x, y = ((x - self.center_x)/self.half_width,
		(self.center_y - y)/self.half_width)
		if (self.xy[0] - x)**2 + (self.xy[1] - y)**2 > self.move_threashold:
			self.xy = x, y
			self.vector(self.xy)
			
	def touch_ended(self, touch):
		self.xy = (0, 0)
		self.vector(self.xy)
		pass
		
class RobotController(object):
	def __init__(self, topv):
		topv.background_color = '#2f2f2f'
		
		v_ipaddress = topv['IP_address']
		v_ipaddress.action = self.enter_ipaddress
		
		v_button_connect = topv['connect']
		v_button_connect.action = self.do_connect
		
		v_button_start = topv['start']
		v_button_start.action = self.do_start
		
		v_button_reset = topv['reset']
		v_button_reset.action = self.do_reset
		
		self.v_message = topv['message']
		
		v_control_pad = topv['control_pad']
		v_control_pad.vector = self._vector
		
	def message(self, text):
		text = self.v_message.text + '\n' + text
		self.v_message.text = text[-500:]

	def _vector(self, xy):
		self.message('%f, %f' % xy)
		
	def enter_ipaddress(self, sender):
		self.v_message.text = sender.text
		
	def do_connect(self, sender):
		pass
		
	def do_start(self, sender):
		pass
		
	def do_reset(self, sender):
		pass
		
v = ui.load_view('drive-ipad')
robot_controller = RobotController(v)
v.present('sheet')

