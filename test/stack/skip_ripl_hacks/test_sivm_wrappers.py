# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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
from nose.tools import assert_equal

from venture.sivm import VentureSivm
from venture.test.config import get_core_sivm
import venture.value.dicts as v

# TODO Not really backend independent, but doesn't test the backend much.
# Almost the same effect as @venture.test.config.in_backend('none'),
# but works on the whole class
@attr(backend='none')
class TestVentureSivm(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.core_sivm = get_core_sivm()
        self.core_sivm.execute_instruction({'instruction':'clear'})
        self.sivm = VentureSivm(self.core_sivm)

    def tearDown(self):
        pass

    def extractValue(self,d): return d['value']['value']

    def testAssume(self):
        did1 = self.sivm.assume('x1',v.number(1))['directive_id']
        self.sivm.assume('x2',v.number(2),label='xx2')
        assert_equal(self.extractValue(self.sivm.report(did1)),1)
        assert_equal(self.extractValue(self.sivm.report('xx2')),2)

    def testPredict(self):
        did1 = self.sivm.predict(v.number(1))['directive_id']
        self.sivm.predict(v.number(2),label='xx2')
        assert_equal(self.extractValue(self.sivm.report(did1)),1)
        assert_equal(self.extractValue(self.sivm.report('xx2')),2)

    def testListDirectives(self):
        self.sivm.predict(v.number(1))
        self.sivm.predict(v.number(2),label='xx2')
        assert_equal(len(self.sivm.list_directives()['directives']),2)

    def testObserve(self):
        self.sivm.observe([v.symbol('normal'), v.number(0), v.number(1)],
                          v.number(1),
                          label='obs')
        assert_equal(self.extractValue(self.sivm.report('obs')),1)

    def testForget(self):
        did1 = self.sivm.predict(v.number(1))['directive_id']
        self.sivm.predict(v.number(2),label='xx2')
        self.sivm.forget(did1)
        self.sivm.forget('xx2')
        assert_equal(len(self.sivm.list_directives()['directives']),0)

    def testForceAndSample(self):
        self.sivm.assume('x',[v.symbol('normal'), v.number(0), v.number(1)])
        self.sivm.force('x',v.number(-2))
        assert_equal(self.extractValue(self.sivm.sample('x')),-2)
