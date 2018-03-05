#!/usr/bin/python3

import sys
sys.path.append('../upy/lib')

import display
display._FontBase.FONTDIR = '../fonts/'

fcf = display.FixedColorFont(sys.argv[1])

for code in range(0x21, 127):
    print(('[ %c ]' % code).center(20, '-'))
    bitmap_r_c = [['.' for _ in range(fcf.WIDTH)] for _ in range(fcf.HEIGHT)]
    pixels, unit_b = fcf.pixels(chr(code))
    for r in range(fcf.HEIGHT):
        for c in range(fcf.WIDTH):
            if pixels[0] != 0:
                bitmap_r_c[r][c] = '#'
            pixels = pixels[2:]
    for row in bitmap_r_c:
        print(''.join(row))
