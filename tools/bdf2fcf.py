import sys
import array

COLORS = (array.array('B', (0, 0)),
          array.array('B', (0xff, 0xff)))

def get_bitmap(fobj):
    v = []
    while True:
        s = fobj.readline().rstrip()
        if len(s) == 2:
            break
        if not s:
            return None
    while True:
        b = int(s, 16) >> 2
        v.append('{:06b}'.format(b))
        s = fobj.readline().rstrip()
        if len(s) != 2:
            return v
        
def scan_bdf(bdf, callback):
    with open(bdf) as f:
        c = 0
        while True:
            bitmap = get_bitmap(f)
            if not bitmap:
                break
            callback(c, bitmap)
            c += 1
            if c == 128:
                return

def save(c, bitmap, fontimg):
    for b in bitmap:
        for c in b:
            fontimg.extend(COLORS[c == '1'])

IN_FILE = 'mplus_f12r.bdf'
OUT_FILE = '../fonts/mplus-65k-13x6.fcf'

fontimg = array.array('B')
scan_bdf(IN_FILE, lambda c, bitmap: save(c, bitmap, fontimg))
with open(OUT_FILE, 'wb') as f:
    f.write(fontimg)
