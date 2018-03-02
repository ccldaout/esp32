import sys
import array

COLORS = (array.array('B', (0, 0)),
          array.array('B', (0xff, 0xff)))

class Bitmap6x13(object):
    WIDTH = 6
    HEIGHT = 13
    BIT_YET = 0
    BIT_SET = 1
    BIT_DONT = -1

    def __init__(self):
        self.map = [array.array('b', (self.BIT_DONT for _ in range(6)))
                    for _ in range(self.HEIGHT)]
        self._row = 0

    def set_row(self, val):
        if self._row >= self.HEIGHT:
            return
        row = self.map[self._row]
        for i in range(self.WIDTH):
            if val & (1<<i):
                row[self.WIDTH-i-1] = self.BIT_YET
        self._row += 1
            
    def scan(self):
        hm = (0, -1, -1, -1)	# max-chg, row, col_beg, col_end
        for r in range(self.HEIGHT):
            # find 1st BIT_YET
            for b in range(self.WIDTH):
                if self.map[r][b] == self.BIT_YET:
                    break
            else:
                continue
            chg = 0
            for e in range(b, self.WIDTH):
                if self.map[r][e] == self.BIT_YET:
                    chg += 1
                elif self.map[r][e] == self.BIT_SET:
                    pass
                else:
                    break
            else:
                e = self.WIDTH
            e -= 1
            if chg > hm[0]:
                hm = (chg, r, b, e)
        if hm[0] == 0:
            return None

        vm = (0, -1, -1, -1)	# max-chg, col, row_beg, row_end
        for c in range(self.WIDTH):
            # find 1st BIT_YET
            for b in range(self.HEIGHT):
                if self.map[b][c] == self.BIT_YET:
                    break
            else:
                continue
            chg = 0
            for e in range(b, self.HEIGHT):
                if self.map[e][c] == self.BIT_YET:
                    chg += 1
                elif self.map[e][c] == self.BIT_SET:
                    continue
                else:
                    break
            else:
                e = self.HEIGHT
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

def get_bitmap(fobj):
    while True:
        s = fobj.readline().rstrip()
        if len(s) == 2:
            break
        if not s:
            return None

    bm = Bitmap6x13()
    while True:
        b = int(s, 16) >> 2
        bm.set_row(b)
        s = fobj.readline().rstrip()
        if len(s) != 2:
            return bm
        
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

#index:
# offset:0..(16bit) 
#font
# c_beg: b0[0:7]: 0..5  (3bit)
# r_beg: b1[0:7]: 0..11 (4bit)
# c_end: b2[0:7]: 0..5  (3bit)
# r_end: b3[0:7]: 0..11 (4bit)

class FontFile(object):
    def __init__(self):
        self._index = array.array('H')
        self._data = array.array('B')
        self._frow = 0

    def font_beg(self):
        self._frow = 0
        self._index.append(len(self._data))

    def font_map(self, bitmap):
        while True:
            line = bitmap.scan()
            if line is None:
                return
            for d in line:
                self._data.append(d)

    def font_end(self):
        pass

    def font(self, c_ord, bitmap):
        self.font_beg()
        self.font_map(bitmap)
        self.font_end()

    def save(self, path):
        self._index.append(len(self._data))
        with open(path, 'wb') as f:
            f.write(self._index)
            f.write(self._data)

IN_FILE = 'mplus_f12r.bdf'
OUT_FILE = '../fonts/mplus-13x6.gcf'

fontfile = FontFile()
scan_bdf(IN_FILE, fontfile.font)
fontfile.save(OUT_FILE)

