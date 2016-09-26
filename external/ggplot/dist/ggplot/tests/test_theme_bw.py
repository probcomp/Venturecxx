from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from nose.tools import assert_true
from ..tests import image_comparison

from ggplot import *


@image_comparison(baseline_images=['theme_bw'], extensions=["png"])
def test_theme_bw1():
    gg = ggplot(aes(x='date', y='beef'), data=meat) + \
        geom_point(color='lightblue') + \
        stat_smooth(span=.15, color='black', se=True) + \
        ggtitle("Beef: It's What's for Dinner") + \
        xlab("Date") + \
        ylab("Head of Cattle Slaughtered")
    gg_theme = gg + theme_bw()
    assert_true(isinstance(gg_theme.theme, theme_bw))
    print(gg_theme)
