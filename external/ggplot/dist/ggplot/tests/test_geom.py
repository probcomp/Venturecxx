from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from nose.tools import assert_equal, assert_is, assert_is_not, assert_raises
from ..tests import image_comparison

from ggplot import *
from ..geoms.geom import geom


def test_geom_basics():
    # mock the validd aes and get the geom to accept the color
    # mapping -> only subclasses normally declare which aes mappings
    # are valid and geom.DEFAULT_AES is a empty list
    geom.DEFAULT_AES = {"color": None}
    geom.DEFAULT_PARAMS = {'stat': 'identity'}
    g = geom(data=meat)
    assert_is(meat, g.data)
    g = geom(meat)
    assert_is(meat, g.data)
    g = geom(aes(color="beef"))
    assert_equal("beef", g.aes["color"])
    g = geom(mapping=aes(color="pork"))
    assert_equal("pork", g.aes["color"])
    with assert_raises(Exception):
        g = geom(aes(color="beef"), mapping=aes(color="pork"))
    assert_equal("pork", g.aes["color"])
    # setting, not mapping
    g = geom(color="blue")
    assert_equal("blue", g.manual_aes["color"])

@image_comparison(baseline_images=['geom_with_data'], extensions=["png"])
def test_geom_with_data_visual():
    gg = ggplot(mtcars, aes("wt", "mpg")) + geom_point()
    g2 = gg + geom_text(aes(label="name"), data=mtcars[mtcars.cyl == 6])
    print(g2)

def test_geom_with_data():
    gg = ggplot(mtcars, aes("wt", "mpg")) + geom_point()
    cols_before = gg.data.columns.copy()
    _text = geom_text(aes(label="name"), data=mtcars[mtcars.cyl == 6])
    g2 = gg + _text
    assert_is_not(g2.data, _text.data, "Adding a dataset to a geom replaced the data in ggplot")

def test_geom_with_invalid_argument():
    with assert_raises(Exception):
        geom_text(write_shakespeare=True)
