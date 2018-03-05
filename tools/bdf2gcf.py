#!/usr/bin/python2

import sys
import array

class BitmapWxH(object):
    BIT_YET = 0
    BIT_SET = 1
    BIT_DONT = -1

    def __init__(self):
        self.map = [array.array('b', (self.BIT_DONT for _ in range(6)))
                    for _ in range(FONT_HEIGHT)]
        self._row = 0

    def set_row(self, val):
        if self._row >= FONT_HEIGHT:
            return
        row = self.map[self._row]
        for i in range(FONT_WIDTH):
            if val & (1<<i):
                row[FONT_WIDTH-i-1] = self.BIT_YET
        self._row += 1
            
    def scan(self):
        hm = (0, -1, -1, -1)	# max-chg, row, col_beg, col_end
        for r in range(FONT_HEIGHT):
            # find 1st BIT_YET
            for b in range(FONT_WIDTH):
                if self.map[r][b] == self.BIT_YET:
                    break
            else:
                continue
            chg = 0
            for e in range(b, FONT_WIDTH):
                if self.map[r][e] == self.BIT_YET:
                    chg += 1
                elif self.map[r][e] == self.BIT_SET:
                    pass
                else:
                    break
            else:
                e = FONT_WIDTH
            e -= 1
            if chg > hm[0]:
                hm = (chg, r, b, e)
        if hm[0] == 0:
            return None

        vm = (0, -1, -1, -1)	# max-chg, col, row_beg, row_end
        for c in range(FONT_WIDTH):
            # find 1st BIT_YET
            for b in range(FONT_HEIGHT):
                if self.map[b][c] == self.BIT_YET:
                    break
            else:
                continue
            chg = 0
            for e in range(b, FONT_HEIGHT):
                if self.map[e][c] == self.BIT_YET:
                    chg += 1
                elif self.map[e][c] == self.BIT_SET:
                    continue
                else:
                    break
            else:
                e = FONT_HEIGHT
            e -= 1
            if chg > vm[0]:
                vm = (chg, c, b, e)

        if hm[0] < vm[0]:
            _, c, b_row, e_row = vm
            for i in range(b_row, e_row+1):
                self.map[i][c] = self.BIT_SET
            return (c, b_row, c, e_row)

        _, r, b_col, e_col = hm
        for i in range(b_col, e_col+1):
            self.map[r][i] = self.BIT_SET
        return (b_col, r, e_col, r)

#index:
# offset:0..(16bit) 
#font
# c_beg: b0[0:7]: 0..5  (3bit)
# r_beg: b1[0:7]: 0..11 (4bit)
# c_end: b2[0:7]: 0..5  (3bit)
# r_end: b3[0:7]: 0..11 (4bit)

class FontFile(object):
    def __init__(self):
        self._index = array.array('H', (0 for _ in range(FONT_CNT+1)))
        self._data = array.array('B')

    def font_beg(self, code):
        self._index[code] = len(self._data)

    def font_map(self, bitmap):
        while True:
            line = bitmap.scan()
            if line is None:
                return
            for d in line:
                self._data.append(d)

    def font_end(self):
        pass

    def font(self, code, bitmap):
        bm = BitmapWxH()
        for b in bitmap:
            bm.set_row(b)
        self.font_beg(code)
        self.font_map(bm)
        self.font_end()

    def save(self, path):
        self._index[FONT_CNT] = len(self._data)
        with open(path, 'wb') as f:
            f.write(array.array('B', (FONT_WIDTH, FONT_HEIGHT)))
            f.write(self._index)
            f.write(self._data)

#----------------------------------------------------------------------------
#----------------------------------------------------------------------------

def get_bitmap(fobj):
    v = []
    while True:
        s = fobj.readline().rstrip()
        if s[:9] == 'ENCODING ':
            code = int(s.split()[1])
            if 0x20 <= code < 128:
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
        v.append(b)
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
    OUT_FILE = '../fonts/misaki_7x4.gcf'
    FONT_WIDTH = 4
    ROW_BEG = 0
    ROW_END = 7
elif font_type == 2:	# 5x10
    IN_FILE = 'mplus_f10r.bdf'
    OUT_FILE = '../fonts/mplus_10x5.gcf'
    FONT_WIDTH = 5
    ROW_BEG = 1
    ROW_END = 11
elif font_type == 3:	# 5x12
    IN_FILE = 'mplus_f12r.bdf'
    OUT_FILE = '../fonts/mplus_12x5.gcf'
    FONT_WIDTH = 5
    ROW_BEG = 1
    ROW_END = 13

#COLORS = (array.array('B', (0, 0)),
#          array.array('B', (0xff, 0xff)))

#PIXEL_SIZE = len(COLORS[0])
FONT_CNT = 128	# 0..127
FONT_HEIGHT = ROW_END - ROW_BEG
#FONT_SIZE = FONT_WIDTH * FONT_HEIGHT * PIXEL_SIZE

BITSHIFT = 8 - FONT_WIDTH
BITFORM = '{:0%db}' % FONT_WIDTH

fontfile = FontFile()
scan_bdf(IN_FILE, fontfile.font)
fontfile.save(OUT_FILE)

