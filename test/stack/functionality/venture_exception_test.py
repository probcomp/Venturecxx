# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import unittest

from nose.plugins.attrib import attr

from venture.exception import VentureException

JSON_EXCEPTION = {
        "exception":"exception_type",
        "message":"everything exploded",
        "data1":1,
        "data2":[1,2,3],
        }

EXCEPTION = 'exception_type'
MESSAGE = 'everything exploded'
DATA = {'data1':1,'data2':[1,2,3]}

# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestVentureException(unittest.TestCase):

    def test_constructor(self):
        e = VentureException(EXCEPTION,
                MESSAGE,**DATA)
        self.assertEqual(e.exception, EXCEPTION)
        self.assertEqual(e.message, MESSAGE)
        self.assertEqual(e.data, DATA)

    def test_to_json_object(self):
        e = VentureException(EXCEPTION,
                MESSAGE,**DATA)
        self.assertEqual(e.to_json_object(),JSON_EXCEPTION)

    def test_from_json_object(self):
        e = VentureException.from_json_object(JSON_EXCEPTION)
        self.assertEqual(e.to_json_object(),JSON_EXCEPTION)


