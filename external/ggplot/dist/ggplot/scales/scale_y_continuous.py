from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from .scale import scale
from copy import deepcopy
from matplotlib.pyplot import FuncFormatter

dollar   = lambda x, pos: '$%1.2f' % x
currency = dollar
comma    = lambda x, pos: '{:0,d}'.format(int(x))
millions = lambda x, pos: '$%1.1fM' % (x*1e-6)
percent  = lambda x, pos: '{0:.0f}%'.format(x*100)

LABEL_FORMATS = {
    'comma': comma,
    'dollar': dollar,
    'currency': currency,
    'millions': millions,
    'percent': percent
}

class scale_y_continuous(scale):
    VALID_SCALES = ['name', 'labels', 'limits', 'breaks', 'trans']
    def __radd__(self, gg):
        gg = deepcopy(gg)
        if self.name:
            gg.ylab = self.name.title()
        if not (self.labels is None):
            if self.labels in LABEL_FORMATS:
                format_func = LABEL_FORMATS[self.labels]
                gg.ytick_formatter = FuncFormatter(format_func)
            else:
                gg.ytick_labels = self.labels
        if not (self.limits is None):
            gg.ylimits = self.limits
        if not (self.breaks is None):
            gg.ybreaks = self.breaks
        return gg

