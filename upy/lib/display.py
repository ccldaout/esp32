import array


#----------------------------------------------------------------------------
#                                   color
#----------------------------------------------------------------------------

class Color(object):
    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    @property
    def bgr(self):
        return (self.b, self.g, self.r)

    @bgr.setter
    def bgr(self, bgr):
        self.b, self, g, self.r = bgr

    @property
    def rgb(self):
        return (self.r, self.g, self.b)

    @rgb.setter
    def rgb(self, rgb):
        self.r, self, g, self.b = rgb
    

#----------------------------------------------------------------------------
#                               font handling
#----------------------------------------------------------------------------

class _FontBase(object):

    FONTDIR = 'fonts/'
    FONTNUM = 128
    PIXELSIZE_b = 2

class FixedColorFont(_FontBase):

    def __init__(self, fontfile='misaki_7x4.fcf'):
        path = self.FONTDIR + fontfile
        with open(path, 'rb') as f:
            wh = array.array('B', (0, 0))
            f.readinto(wh)
            self.WIDTH = wh[0]
            self.HEIGHT = wh[1]
            self._fontunit_b = self.WIDTH * self.HEIGHT * self.PIXELSIZE_b
            size = self._fontunit_b * self.FONTNUM
            self._fontarray = memoryview(array.array('B', (0 for _ in range(size))))
            f.readinto(self._fontarray)

    def change_color(self, fg_pixel, bg_pixel):
        if fg_pixel or bg_pixel:
            fa = self._fontarray
            for i in range(0, size, 2):
                if fa[i]:
                    fa[i:i+2] = fg_pixel
                else:
                    fa[i:i+2] = bg_pixel

    def pixels(self, c):
        fbeg = self._fontunit_b * ord(c)
        fend = fbeg + self._fontunit_b
        return (self._fontarray[fbeg:fend], self._fontunit_b)

class GraphicCompositFont(_FontBase):

    def __init__(self, fontfile='mplus_10x5.gcf'):
        path = self.FONTDIR + fontfile
        with open(path, 'rb') as f:
            wh = array.array('B', (0, 0))
            f.readinto(wh)
            self.WIDTH = wh[0]
            self.HEIGHT = wh[1]
            self._index = array.array('H', range(self.FONTNUM + 1))
            f.readinto(self._index)
            dsize = self._index[-1]
            self._data = memoryview(array.array('B', (0 for _ in range(dsize))))
            f.readinto(self._data)

    def get_line(self, c):
        obeg = self._index[ord(c)]
        oend = self._index[ord(c)+1]
        while obeg < oend:
            omid = obeg + 4
            yield self._data[obeg:omid]
            obeg = omid


#----------------------------------------------------------------------------
#                                   image
#----------------------------------------------------------------------------

class Image(object):

    def __init__(self, img_file=None, w=None, h=None):
        if img_file:
            size = array.array('B', (0, 0))
            with open(img_file, 'rb') as f:
                f.readinto(size)
                w, h = size
                imgbuf = array.array('B', range(w * h * 2))
                f.readinto(imgbuf)
        else:
            imgbuf = array.array('B', (0 for _ in range(w * h * 2)))
            self.append = imgbuf.append
            self.extend = imgbuf.extend
        self.w = w
        self.h = h
        self.buf = imgbuf


#----------------------------------------------------------------------------
#                               adaptor base
#----------------------------------------------------------------------------

class AdaptorBase(object):

    def __new__(cls, *, use_fcf, use_gcf):
        self = super().__new__(cls)

        # fonts
        if use_fcf:
            self.fcf = FixedColorFont()
        if use_gcf:
            self.gcf = GraphicCompositFont()
        
        # colors: public properties
        self.line_color = Color(0, 0, 0)	# RGB
        self.fill_color = Color(0, 0, 0)	# RGB
        self.gcf_fg_color = Color(0, 0, 0)
        self.gcf_bg_color = None

        #
        self.Color = Color
        self.Image = Image

        return self

    @property
    def display_size(self):
        raise NotImplementedError()

    @property
    def fcf_size(self):
        return (self.fcf.WIDTH, self.fcf.HEIGHT)

    @property
    def gcf_size(self):
        return (self.gcf.WIDTH, self.gcf.HEIGHT)

    def fcf_change_color(self, fg_pixel, bg_pixel):
        raise NotImplementedError()

    def pixel(self, r, g, b):
        raise NotImplementedError()

    def clear(self,
              col_start=0, row_start=0,
              col_end=95, row_end=63):
        raise NotImplementedError()

    def draw_image(self, col, row, imgbuf):
        raise NotImplementedError()

    def draw_line(self,
                  col_start, row_start,
                  col_end, row_end):
        raise NotImplementedError()

    def draw_rect(self,
                  col_start, row_start,
                  col_end, row_end):
        raise NotImplementedError()

    def fcf_put(self, col, row, chars):
        raise NotImplementedError()

    def gcf_put(self, col, row, chars):
        raise NotImplementedError()
