# -*- coding: utf-8 -*-

import sys
import array
from PIL import Image

if len(sys.argv) != 3:
    print 'Usage: %s input_image 16bit_color_img' % sys.argv[0]
    exit()

org = Image.open(sys.argv[1])

width = org.size[0]
height = org.size[1]

print 'size WxH:', width, height

def conv_rgb(r, g, b):
    return (r >> 3,
            g >> 2,
            b >> 3)

def pixel_64k1(buf, r, g, b):
    buf.append(((0x1f & r)<<3)|((0x3f & g)>>3))
    buf.append(((0x7 & g)<<5)|(0x1f & b))

buf = array.array('B')
buf.append(width)
buf.append(height)

for y in xrange(height):
    for x in xrange(width):
        px = org.getpixel((x, y))
        pixel_64k1(buf, *conv_rgb(*px[:3]))

with open(sys.argv[2], 'wb') as f:
    f.write(buf)
