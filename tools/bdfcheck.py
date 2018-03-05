import sys
import array

def show(code, bitmap):
    print ('[ %c (%d) ]' % (code, code)).center(20, '-')
    for bits in bitmap:
        print bits.replace('0', '.').replace('1', '#')

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def get_bitmap(fobj):
    v = []
    while True:
        s = fobj.readline().rstrip()
        if s[:9] == 'ENCODING ':
            code = int(s.split()[1])
            if 0x20 <= code < FONT_CNT:
                break
        if not s:
            return None, None
    while True:
        s = fobj.readline().rstrip()
        if len(s) == 2:
            break
        if not s:
            return None, None
    while True:
        b = int(s, 16) >> BITSHIFT
        v.append(BITFORM.format(b))
        s = fobj.readline().rstrip()
        if len(s) != 2:
            return code, v
        
def scan_bdf(bdf, callback):
    with open(bdf) as f:
        while True:
            code, bitmap = get_bitmap(f)
            if not bitmap:
                break
            callback(code, bitmap[ROW_BEG:ROW_END])

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

font_type = int(sys.argv[1])

if font_type == 1:	# 4x7
    IN_FILE = 'misaki_4x8_iso8859.bdf'
    OUT_FILE = '../fonts/misaki_7x4.fcf'
    FONT_WIDTH = 4
    ROW_BEG = 0
    ROW_END = 7
elif font_type == 2:	# 5x10
    IN_FILE = 'mplus_f10r.bdf'
    OUT_FILE = '../fonts/mplus_10x5.fcf'
    FONT_WIDTH = 5
    ROW_BEG = 1
    ROW_END = 11
elif font_type == 3:	# 5x12
    IN_FILE = 'mplus_f12r.bdf'
    OUT_FILE = '../fonts/mplus_12x5.fcf'
    FONT_WIDTH = 5
    ROW_BEG = 1
    ROW_END = 13

FONT_CNT = 128	# 0..127
FONT_HEIGHT = ROW_END - ROW_BEG

BITSHIFT = 8 - FONT_WIDTH
BITFORM = '{:0%db}' % FONT_WIDTH

scan_bdf(IN_FILE, show)
