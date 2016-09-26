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
from nose import SkipTest

from venture.exception import VentureException
from venture.sivm import VentureSivm
from venture.test.config import get_core_sivm
import venture.value.dicts as v

# TODO Maybe implement a stub backend that answers all method calls
# with "Yes, Minister" and use that instead of Lite here.
# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestVentureSivm(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.core_sivm = get_core_sivm()
        self.core_sivm.execute_instruction({'instruction':'clear'})
        self.sivm = VentureSivm(self.core_sivm)

    def tearDown(self):
        pass

    def test_missing_instruction(self):
        try:
            self.sivm.execute_instruction({})
        except VentureException as e:
            self.assertEqual(e.exception,'malformed_instruction')
    def test_missing_argument(self):
        try:
            self.sivm.execute_instruction({
                'instruction':'assume',
                'symbol':"MOO"
                })
        except VentureException as e:
            self.assertEqual(e.exception,'missing_argument')
            self.assertEqual(e.data['argument'],'expression')
    def test_invalid_argument(self):
        try:
            self.sivm.execute_instruction({
                'instruction':'assume',
                'symbol':v.symbol("9,d"),
                'expression':['a','b',['c']]
                })
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'symbol')
    def test_invalid_label(self):
        inst = {
                'instruction':'labeled_assume',
                'expression': ['add',v.number(1),v.number(2)],
                'symbol': v.symbol('moo'),
                'label': v.symbol('123moo')
                }
        try:
            self.sivm.execute_instruction(inst)
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'label')
    def test_repeated_label(self):
        inst = {
                'instruction':'labeled_assume',
                'expression': ['add',v.number(1),v.number(2)],
                'symbol': v.symbol('moo'),
                'label': v.symbol('moo')
                }
        self.sivm.execute_instruction(inst)
        try:
            self.sivm.execute_instruction(inst)
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'label')

    # test expression desugaring and exception sugaring
    def test_sugaring_1(self):
        raise SkipTest("Stubbing the sivm breaks pausing continuous inference.  Issue: https://app.asana.com/0/9277419963067/10281673660714")
        #stub the Sivm
        def f(expression):
            raise VentureException('parse', 'moo', expression_index=[3,2,0,1,0])
        self.core_sivm.execute_instruction = f
        try:
            self.sivm.execute_instruction({
                'instruction':'assume',
                'symbol':"d",
                'expression':['if','a','b',['let',[['c','d']],'e']]
                })
        except VentureException as e:
            self.assertEqual(e.exception,'parse')
            self.assertEqual(e.data['expression_index'],[3,1,0,0])

    # just make sure these don't crash
    def test_labeled_assume(self):
        inst = {
                'instruction':'labeled_assume',
                'expression': ['add',v.number(1),v.number(2)],
                'symbol': v.symbol('moo'),
                'label' : v.symbol('moo')
                }
        val = v.number(3)
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)
    def test_labeled_observe(self):
        inst = {
                'instruction':'labeled_observe',
                'expression': ['normal',v.number(1),v.number(2)],
                'value': v.real(3),
                'label' : v.symbol('moo')
                }
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
    def test_labeled_predict(self):
        inst = {
                'instruction':'labeled_predict',
                'expression': ['add',v.number(1),v.number(2)],
                'label' : v.symbol('moo')
                }
        val = v.number(3)
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)
    def test_labeled_forget(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',v.number(1),v.number(2)],
                'label' : v.symbol('moo'),
                }
        self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'labeled_forget',
                'label' : v.symbol('moo'),
                }
        self.sivm.execute_instruction(inst2)
        try:
            self.sivm.execute_instruction(inst2)
        except VentureException as e:
            self.assertEquals(e.exception,'invalid_argument')
        o3 = self.sivm.list_directives()
        self.assertEquals(o3, [])
    def test_labeled_report(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',v.number(1),v.number(2)],
                'label' : 'moo',
                }
        self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'labeled_report',
                'label' : v.symbol('moo'),
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['value'], v.number(3))
    def test_list_directives(self):
        inst1 = {
                'instruction':'predict',
                'expression': [v.symbol('add'),v.number(1),v.number(2)],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst1['directive_id'] = o1['directive_id']
        o2 = self.sivm.list_directives()
        self.assertEquals(o2, [inst1])
    def test_get_directive(self):
        inst1 = {
                'instruction':'predict',
                'expression': [v.symbol('add'),v.number(1),v.number(2)],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst1['directive_id'] = o1['directive_id']
        o2 = self.sivm.get_directive(o1['directive_id'])
        self.assertEquals(o2, inst1)
    def test_labeled_get_directive(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': [v.symbol('add'),v.number(1),v.number(2)],
                'label': v.symbol('moo'),
                }
        o1 = self.sivm.execute_instruction(inst1)
        del inst1['label']
        o2 = self.sivm.labeled_get_directive(v.symbol('moo'))
        output = {
                'directive_id': o1['directive_id'],
                'instruction': 'predict',
                'expression': [v.symbol('add'),v.number(1),v.number(2)],
                'label': v.symbol('moo'),
                }
        self.assertEquals(o2, output)
    def test_force(self):
        inst = {
                'instruction':'force',
                'expression': ['normal',v.number(1),v.number(2)],
                'value': v.real(3)
                }
        self.sivm.execute_instruction(inst)
        o2 = self.sivm.list_directives()
        self.assertEquals(o2, [])
    def test_sample(self):
        inst = {
                'instruction':'sample',
                'expression': ['add',v.number(1),v.number(2)],
                }
        val = v.number(3)
        o = self.sivm.execute_instruction(inst)
        self.assertEquals(o['value'],val)
        o2 = self.sivm.list_directives()
        self.assertEquals(o2, [])
