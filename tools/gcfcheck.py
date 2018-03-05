#!/usr/bin/python3

import sys
sys.path.append('../upy/lib')

import display
display._FontBase.FONTDIR = '../fonts/'

gcf = display.GraphicCompositFont(sys.argv[1])

for code in range(0x21, 127):
    print(('[ %c ]' % code).center(20, '-'))
    bitmap_r_c = [['.' for _ in range(gcf.WIDTH)] for _ in range(gcf.HEIGHT)]
    for c_beg, r_beg, c_end, r_end in gcf.get_line(chr(code)):
        for r in range(r_beg, r_end+1):
            for c in range(c_beg, c_end+1):
                bitmap_r_c[r][c] = '#'
    for row in bitmap_r_c:
        print(''.join(row))
