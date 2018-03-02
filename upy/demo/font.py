import array
import math
import os
import ssd1331
import time

IMGFILE = 'data/demo_d.sample.img'

DISP_H = 64
DISP_W = 92

driver = ssd1331.vspi()
driver.set_remap_and_color_depth(column_reverse_order=True,
                                 scan_reverse_on_COM=True)
driver.enable_fill()

disp = ssd1331.Adaptor(driver, fcf=True, gcf=True)

def demo():
    print('disp OK', time.ticks_ms())
    img = disp.Image(IMGFILE)
    disp.draw_image((DISP_W-img.w)//2, (DISP_H-img.h)//2, img)
    print('image OK', time.ticks_ms())

    disp.fcf_put(1, 1, 'Hello')
    disp.fcf_put(13, 13, 'World !')

    disp.gcf_fg_color = disp.Color(20, 0, 0)
    disp.gcf_bg_color = disp.Color(0, 10, 10)
    disp.gcf_put(1, 41, 'Hello')

    disp.gcf_fg_color = disp.Color(10, 5, 25)
    disp.gcf_bg_color = None
    disp.gcf_put(13, 53, 'World !')

def speed(n, put, s):
    tv_us = time.ticks_us()
    for _ in range(n):
        put(2, 30, s)
    print(time.ticks_us() - tv_us)
