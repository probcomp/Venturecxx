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
import unittest
from nose import SkipTest
from nose.plugins.attrib import attr

import venture.sivm.core_sivm as module
from venture.exception import VentureException
from venture.test.config import get_core_sivm
import venture.value.dicts as v

# TODO Not really backend independent, but doesn't test the backend much.
# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestCoreSivm(unittest.TestCase):

    _multiprocess_can_split_ = True

    def setUp(self):
        self.sivm = get_core_sivm()
        self.sivm.execute_instruction({"instruction":"clear"})

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
                "symbol":v.symbol("MOO")
                })
        except VentureException as e:
            self.assertEqual(e.exception,'missing_argument')
            self.assertEqual(e.data['argument'],'expression')
    def test_invalid_argument(self):
        try:
            self.sivm.execute_instruction({
                "instruction":"assume",
                "symbol":v.symbol("9,d"),
                "expression":['a','b',['c']]
                })
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'symbol')

    def test_modify_value(self):
        val = v.val("count", 1)
        s = v.number(1)
        self.assertEqual(module._modify_value(val),s)

    def test_modify_symbol(self):
        val = 'add'
        s = v.symbol('add')
        self.assertEqual(module._modify_symbol(val),s)

    def test_modify_expression(self):
        exp= ['sub', v.real(2), 'a']
        s = [v.symbol('sub'), v.number(2), v.symbol('a')]
        self.assertEqual(module._modify_expression(exp),s)

    def test_assume(self):
        inst = {
                'instruction':'assume',
                'expression': ['add',v.number(1),v.number(2)],
                'symbol': v.symbol('moo')
                }
        val = v.number(3)
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)

    def test_observe(self):
        inst = {
                'instruction':'observe',
                'expression': ['normal',v.number(1),v.number(2)],
                'value': v.real(3)
                }
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
    def test_observe_fail(self):
        raise SkipTest("Engine should report a polite exception on constraint of a deterministic choice.  Issue: https://app.asana.com/0/9277419963067/9940667562268")
        inst = {
                'instruction':'observe',
                'expression': ['add',v.number(1),v.number(2)],
                'value': v.real(4)
                }
        try:
            self.sivm.execute_instruction(inst)
        except VentureException as e:
            self.assertEquals(e.exception, 'invalid_constraint')

    def test_predict(self):
        inst = {
                'instruction':'predict',
                'expression': ['add',v.number(1),v.number(2)],
                }
        val = v.number(3)
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)

    def test_configure(self):
        inst = {
                'instruction':'configure',
                'options':{
                    'inference_timeout':5000,           # inference timeout hook is not implemented
                    'seed':0,
                    },
                }

        o = self.sivm.execute_instruction(inst)
        self.assertEquals(o['options']['inference_timeout'],5000)
        # FIXME: seed is always returned as 0
        self.assertEquals(o['options']['seed'],0)

    def test_forget(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',v.number(1),v.number(2)],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'forget',
                'directive_id':o1['directive_id'],
                }
        
        self.sivm.execute_instruction(inst2)

        try:
            self.sivm.execute_instruction(inst2)
        except VentureException as e:
            self.assertEquals(e.exception,'invalid_argument')

    def test_report(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',v.number(1),v.number(2)],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'report',
                'directive_id':o1['directive_id'],
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['value'], v.number(3))
    def test_report_invalid_did(self):
        inst = {
                'instruction':'report',
                'directive_id':123456,
                }
        try:
            self.sivm.execute_instruction(inst)
        except VentureException as e:
            self.assertEquals(e.exception,'invalid_argument')

    def test_infer(self):
        inst = {
                'instruction':'infer',
                'expression': [v.sym("mh"), v.sym("default"), v.sym("one"), v.num(2)]
                }
        self.sivm.execute_instruction(inst)

    def test_clear(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add', v.num(1), v.num(2)],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'clear',
                }
        self.sivm.execute_instruction(inst2)
        inst = {
                'instruction':'report',
                'directive_id':o1['directive_id'],
                }
        try:
            self.sivm.execute_instruction(inst)
        except VentureException as e:
            self.assertEquals(e.exception,'invalid_argument')

    def test_rollback(self):
        raise SkipTest("Engine should report a polite exception on unbound variable.  Issue: https://app.asana.com/0/9277419963067/9940667562266")
        inst1 = {
                'instruction':'observe',
                'expression': 'aweopfjiaweopfaweopfjopawejiawoiejf',
                'value':v.number(3)
                }
        try:
            self.sivm.execute_instruction(inst1)
        except VentureException as e:
            self.assertEquals(e.exception,'evaluation')
        self.assertEquals(self.sivm.state,'exception')
        inst2 = {
                'instruction':'rollback',
                }
        self.sivm.execute_instruction(inst2)
        self.assertEquals(self.sivm.state,'default')

    def test_get_global_logscore(self):
        inst1 = {
                'instruction':'observe',
                'expression': ['flip'],
                'value': v.boolean(True)
                }
        self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'get_global_logscore',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['logscore'],-0.6931471805599453)
    
    def test_continuous_inference(self):
        status = {'instruction':'continuous_inference_status'}
        o1 = self.sivm.execute_instruction(status)
        self.assertEquals(o1['running'], False)
        
        exp = [v.sym("mh"), v.sym("default"), v.sym("one"), v.num(2)]
        self.sivm.execute_instruction({'instruction':'start_continuous_inference', 'expression' : exp})
        o2 = self.sivm.execute_instruction(status)
        self.assertEquals(o2['running'], True)
        
        self.sivm.execute_instruction({'instruction':'stop_continuous_inference'})
        o3 = self.sivm.execute_instruction(status)
        self.assertEquals(o3['running'], False)
    
    def test_profiler_configure(self):
        i1 = {'instruction':'profiler_configure', 'options': {}}
        o1 = self.sivm.execute_instruction(i1)
        e1 = {'options': {'profiler_enabled': False}}
        self.assertEquals(o1, e1)
        
        i2 = {'instruction':'profiler_configure', 'options': {'profiler_enabled': True}}
        o2 = self.sivm.execute_instruction(i2)
        e2 = {'options': {'profiler_enabled': True}}
        self.assertEquals(o2, e2)

        i3 = {'instruction':'profiler_configure', 'options': {'profiler_enabled': False}}
        o3 = self.sivm.execute_instruction(i3)
        e3 = {'options': {'profiler_enabled': False}}
        self.assertEquals(o3, e3)

