import array
import math
import os
import time

import sensor
import servo
import ssd1331


HALF_ANGLE = 45		# one side angle
DISP_H = 64		# Display horizontal size
DISP_W = 92		# Display vertical size

TRIG_PIN = 32		# HCSR04: Trigger pin
ECHO_PIN = 25		# HSCR04: Echo pin
H_PIN_NUM = 27		# Mounter(SG90): pin of Horizontal motor

SENSOR_OFFSET_cm = 4.0


#----------------------------------------------------------------------------
#                                  Sensor
#----------------------------------------------------------------------------


#----------------------------------------------------------------------------
#                                  Mounter
#----------------------------------------------------------------------------

def deg2rad(deg):
    return math.pi * (deg / 180.0)

class Mounter(object):

    def __init__(self, h_pin_num):
        self._hservo = servo.ServoSG90(h_pin_num)
        self._duty_min = self._hservo.duty_by_angle(-HALF_ANGLE)
        self._duty_0   = self._hservo.duty_by_angle(0)
        duty_hrange = self._duty_0 - self._duty_min
        self._duty_max = self._duty_0 + duty_hrange
        rabs = deg2rad(HALF_ANGLE)
        self._cossin_tab = [(math.cos(r), math.sin(r))
                            for r in (rabs * (i / duty_hrange)
                                      for i in range(-duty_hrange, duty_hrange + 1))]
        
    def init_cossin(self):
        return self._cossin_tab[0]

    def scan(self, callback, wait_s):
        duty_min = self._duty_min
        duty_max = self._duty_max
        duty_0   = self._duty_0
        cossin_tab = self._cossin_tab

        range_args = ((duty_min, duty_max+1, 1), (duty_max, duty_min-1, -1))
        range_dir = False

        self._hservo.duty(self._duty_min)
        while True:
            for duty in range(*range_args[int(range_dir)]):
                self._hservo.duty(duty)
                time.sleep(wait_s)
                callback(duty - duty_0, *cossin_tab[duty - duty_min])
            range_dir = not range_dir


#----------------------------------------------------------------------------
#                                  Drawer
#----------------------------------------------------------------------------

Color = ssd1331.Color

_OBJ_PERIOD = 20
_SNS_PERIOD = 5
RADER_BG_RGB = Color(0, 0, 1)
RADER_SENSOR_RGB = ([RADER_BG_RGB for _ in range(_OBJ_PERIOD - _SNS_PERIOD)] +
                    [Color(0, 0, n+2) for n in range(_SNS_PERIOD)])
RADER_OBJECT_RGB = [RADER_BG_RGB] + [Color(n, 0, 0) for n in range(1, _OBJ_PERIOD)]

class Drawer(object):

    def __init__(self):
        self._range_min_cm = 2.0
        self._range_max_cm = 50.0
        self._driver = ssd1331.vspi()
        self._driver.color_65k()
        self._driver.enable_fill()
        self._driver.set_remap_and_color_depth(column_reverse_order=True,
                                               scan_reverse_on_COM=True)
        self._disp = ssd1331.Adaptor(self._driver)
        self._disp.clear()
        self.init_rader()

    def init_rader(self):
        H = DISP_W//2 - 1
        R = H * 1.414
        RI = int(R)

        draw_line = self._disp.draw_line

        def h_lines():
            hw = DISP_W//2
            for h in range(RI, H, -1):
                w = int(round(math.sin(math.acos(h/R)) * R))
                yield (DISP_H - h, hw - w, hw + w)
            for h in range(H, 0, -1):
                w = h
                yield (DISP_H - h, hw - w, hw + w)

        for y, xb, xe in h_lines():
            draw_line(xb, y, xe, y, RADER_BG_RGB)

    def set_range(self, min_cm, max_cm):
        self._range_min_cm = min_cm
        self._range_max_cm = max_cm

    def get_updater(self, init_cos, init_sin):
        origin_x, origin_y = DISP_W//2, DISP_H-1
        radius = (DISP_W//2 - 1) * 1.414
        draw_line = self._disp.draw_line
        min_cm = self._range_min_cm
        max_cm = self._range_max_cm
        r_unit = radius / max_cm
        points = [(None, None, None, None) for _ in range(len(RADER_OBJECT_RGB)-1)]

        def update(cos, sin, distance):
            edge_x = origin_x + int(radius * sin)
            edge_y = origin_y - int(radius * cos)
            if min_cm < distance < max_cm:
                obj_x = origin_x + int(r_unit * distance * sin)
                obj_y = origin_y - int(r_unit * distance * cos)
            else:
                obj_x = obj_y = None
            points.append((obj_x, obj_y, edge_x, edge_y))
            px, py = None, None
            for i, (_, _, ex, ey) in enumerate(points):
                if ex is not None:
                    draw_line(ex, ey, origin_x, origin_y, RADER_SENSOR_RGB[i])
                if px is not None:
                    draw_line((px+ex)//2, (py+ey)//2, origin_x, origin_y, RADER_SENSOR_RGB[i])
                px, py = ex, ey
            for i, (ox, oy, _, _) in enumerate(points):
                if ox is not None:
                    draw_line(ox, oy, ox, oy, RADER_OBJECT_RGB[i])
            points.pop(0)

        return update

#----------------------------------------------------------------------------
#                                   Rader
#----------------------------------------------------------------------------

class Rader(object):

    def __init__(self):
        self._sensor = sensor.HCSR04(TRIG_PIN, ECHO_PIN)
        self._sensor.tmo_us = 10*1000
        self._mounter = Mounter(H_PIN_NUM)
        self._drawer = Drawer()

    def _get_callback(self):
        measure = self._sensor.measure
        updater = self._drawer.get_updater(*self._mounter.init_cossin())
        def action(duty_index, cos, sin):
            d = measure()
            updater(cos, sin, 0 if d is None else d + SENSOR_OFFSET_cm)
        return action

    def scan(self, wait_s=0.05, display_range=30.0):
        self._drawer.set_range(SENSOR_OFFSET_cm+2.0, display_range)
        self._mounter.scan(self._get_callback(), wait_s)

rader = Rader()

def demo(wait_s=0.08, display_range=30.0):
    rader.scan(wait_s, display_range)

print('demo(wait_s=0.08, display_range=30.0)')
