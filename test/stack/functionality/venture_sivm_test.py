# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
from nose.plugins.attrib import attr
import unittest

from venture.sivm import CoreSivm, VentureSivm
from venture.exception import VentureException
from nose import SkipTest

# Note -- these tests only check for minimum functionality

# TODO Maybe implement a stub backend that answers all method calls
# with "Yes, Minister" and use that instead of Lite here.
# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestVentureSivm(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        from venture.lite import engine
        self.core_sivm = CoreSivm(engine.Engine())
        self.core_sivm.execute_instruction({"instruction":"clear"})
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
                "instruction":"assume",
                "symbol":"MOO"
                })
        except VentureException as e:
            self.assertEqual(e.exception,'missing_argument')
            self.assertEqual(e.data['argument'],'expression')
    def test_invalid_argument(self):
        try:
            self.sivm.execute_instruction({
                "instruction":"assume",
                "symbol":"9,d",
                "expression":['a','b',['c']]
                })
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'symbol')
    def test_invalid_label(self):
        inst = {
                'instruction':'labeled_assume',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'symbol': 'moo',
                'label': '123moo'
                }
        try:
            self.sivm.execute_instruction(inst)
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'label')
    def test_repeated_label(self):
        inst = {
                'instruction':'labeled_assume',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'symbol': 'moo',
                'label': 'moo'
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
                "instruction":"assume",
                "symbol":"d",
                "expression":['if','a','b',['let',[['c','d']],'e']]
                })
        except VentureException as e:
            self.assertEqual(e.exception,'parse')
            self.assertEqual(e.data['expression_index'],[3,1,0,0])
    # test exception_index desugaring
    def test_sugaring_2(self):
        raise SkipTest("Stubbing the sivm breaks pausing continuous inference.  Issue: https://app.asana.com/0/9277419963067/10281673660714")
        num = {'type':'number','value':1}
        did = self.sivm.execute_instruction({
            "instruction":"assume",
            "symbol":"d",
            "expression":['if',num,num,['let',[['a',num]],num]]
            })['directive_id']
        #stub the Sivm
        def f(expression):
            got = expression['source_code_location']['expression_index']
            expected = [0,3,2,0,1,0]
            self.assertEqual(got,expected)
            return {"breakpoint_id":14}
        self.core_sivm.execute_instruction = f
        self.sivm.execute_instruction({
            "instruction":"debugger_set_breakpoint_source_code_location",
            "source_code_location": {
                "directive_id" : did,
                "expression_index" : [3,1,0,0],
                }
            })

    # just make sure these don't crash
    def test_labeled_assume(self):
        inst = {
                'instruction':'labeled_assume',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'symbol': 'moo',
                'label' : 'moo'
                }
        val = {'type':'number','value':3}
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)
    def test_labeled_observe(self):
        inst = {
                'instruction':'labeled_observe',
                'expression': ['normal',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":3},
                'label' : 'moo'
                }
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
    def test_labeled_predict(self):
        inst = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label' : 'moo'
                }
        val = {'type':'number','value':3}
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)
    def test_labeled_forget(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label' : 'moo',
                }
        self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'labeled_forget',
                'label' : 'moo',
                }
        self.sivm.execute_instruction(inst2)
        try:
            self.sivm.execute_instruction(inst2)
        except VentureException as e:
            self.assertEquals(e.exception,'invalid_argument')
        inst3 = {
                'instruction':'list_directives',
                }
        o3 = self.sivm.execute_instruction(inst3)
        self.assertEquals(o3['directives'], [])
    def test_labeled_report(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label' : 'moo',
                }
        self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'labeled_report',
                'label' : 'moo',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['value'], {'type':'number','value':3})
    def test_labeled_get_logscore(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label' : 'moo',
                }
        self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'labeled_get_logscore',
                'label' : 'moo',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['logscore'],0.0)
    def test_list_directives(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst1['directive_id'] = o1['directive_id']
        inst2 = {
                'instruction':'list_directives',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['directives'], [inst1])
    def test_get_directive(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst1['directive_id'] = o1['directive_id']
        inst2 = {
                'instruction':'get_directive',
                'directive_id':o1['directive_id'],
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['directive'], inst1)
    def test_labeled_get_directive(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label': 'moo',
                }
        o1 = self.sivm.execute_instruction(inst1)
        del inst1['label']
        inst2 = {
                'instruction':'labeled_get_directive',
                'label': 'moo',
                }
        o2 = self.sivm.execute_instruction(inst2)
        output = {
                'directive_id': o1['directive_id'],
                'instruction': 'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label': 'moo',
                }
        self.assertEquals(o2['directive'], output)
    def test_force(self):
        inst = {
                'instruction':'force',
                'expression': ['normal',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":3}
                }
        self.sivm.execute_instruction(inst)
        inst2 = {
                'instruction':'list_directives',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['directives'], [])
    def test_sample(self):
        inst = {
                'instruction':'sample',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        val = {'type':'number','value':3}
        o = self.sivm.execute_instruction(inst)
        self.assertEquals(o['value'],val)
        inst2 = {
                'instruction':'list_directives',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['directives'], [])
        
    def test_get_current_exception(self):
        raise SkipTest("cxx -> python exceptions not implemented.  Issue: https://app.asana.com/0/9277419963067/9940667562266")
        inst1 = {
                'instruction':'force',
                'expression': ['moo',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":3}
                }
        try:
            self.sivm.execute_instruction(inst1)
        except VentureException:
            pass
        inst2 = {
                'instruction':'get_current_exception',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEqual(o2['exception']['exception'], 'evaluation')
    def test_get_state(self):
        inst1 = {
                'instruction':'get_state',
                }
        o1 = self.sivm.execute_instruction(inst1)
        self.assertEqual(o1['state'], 'default')
    def test_reset(self):
        #TODO: write an actual test for reset
        inst1 = {
                'instruction':'reset',
                }
        self.sivm.execute_instruction(inst1)
    def test_debugger_list_breakpoints_and_debugger_get_breakpoint(self):
        raise SkipTest("Breakpoints not implemented.  Issue: https://app.asana.com/0/9277419963067/9280122191539")
        #stub the Sivm
        def f(_):
            return {"breakpoint_id":14}
        self.core_sivm.execute_instruction = f
        inst1 = {
            "instruction":"debugger_set_breakpoint_address",
            "address": "fefefefefefefe",
            }
        o1 = self.sivm.execute_instruction(inst1)
        del inst1['instruction']
        inst1['breakpoint_id'] = o1['breakpoint_id']
        inst2 = {
                'instruction' : 'debugger_list_breakpoints',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEqual(o2['breakpoints'], [inst1])
        inst3 = {
                'instruction' : 'debugger_get_breakpoint',
                'breakpoint_id' : o1['breakpoint_id'],
                }
        o3 = self.sivm.execute_instruction(inst3)
        self.assertEqual(o3['breakpoint'], inst1)



