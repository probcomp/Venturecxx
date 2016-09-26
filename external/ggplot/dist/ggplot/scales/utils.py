from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import numpy as np
import math

def drange(start, stop, step):
    """Compute the steps in between start and stop

    Only steps which are a multiple of `step` are used.

    """
    r = ((start // step) * step) + step # the first step higher than start
    # all subsequent steps are multiple of "step"!
    while r < stop:
        yield r
        r += step

def convert_if_int(x):
    if int(x)==x:
        return int(x)
    else:
        return x

def convertable_to_int(x):
    if int(x)==x:
        return True
    else:
        return False


def calc_axis_breaks_and_limits(minval, maxval, nlabs=None):
    """Calculates axis breaks and suggested limits.

    The limits are computed as minval/maxval -/+ 1/3 step of ticks.

    Parameters
    ----------
    minval : number
      lowest value on this axis
    maxval : number
      higest number on this axis
    nlabs : int
      number of labels which should be displayed on the axis
      Default: None
    """
    if nlabs is None:
        diff = maxval - minval
        base10 = math.log10(diff)
        power = math.floor(base10)
        base_unit = 10**power
        step = base_unit / 2
    else:
        diff = maxval - minval
        tick_range = diff / float(nlabs)
        # make the tick range nice looking...
        power = math.ceil(math.log(tick_range, 10))
        step = np.round(tick_range / (10**power), 1) * 10**power

    labs = list(drange(minval-(step/3), maxval+(step/3), step))

    if all([convertable_to_int(lab) for lab in labs]):
        labs = [convert_if_int(lab) for lab in labs]

    return labs, minval-(step/3), maxval+(step/3)
