import unittest
from venture.sivm import CoreSivmCxx
import venture.sivm.core_sivm_cxx as module
from venture.exception import VentureException

#Note -- these tests only check for minimum functionality

class TestCoreSivmCxx(unittest.TestCase):

    def setUp(self):
        self.sivm = CoreSivmCxx()
        self.sivm.execute_instruction({"instruction":"clear"})
        print "\nIn method " + self._testMethodName

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

    def test_modify_value(self):
        v = {"type":"count", "value":1}
        s = {"type":"number", "value":1}
        self.assertEqual(module._modify_value(v),s)

    def test_modify_symbol(self):
        v = 'add'
        s = {'type': 'symbol', 'value': 'plus'}
        self.assertEqual(module._modify_symbol(v),s)

    def test_modify_expression(self):
        v = ['sub',{"type":"real","value":2},'a']
        s = [{'type': 'symbol', 'value': 'minus'},{"type":"number","value":2},{'type': 'symbol', 'value': 'a'}]
        self.assertEqual(module._modify_expression(v),s)

    def test_assume(self):
        inst = {
                'instruction':'assume',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'symbol': 'moo'
                }
        val = {'type':'number','value':3}
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)

    def test_observe(self):
        inst = {
                'instruction':'observe',
                'expression': ['normal',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":3}
                }
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
    def test_observe_fail(self):
        # engine can only constrain random choices
        return
        inst = {
                'instruction':'observe',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":4}
                }
        try:
            self.sivm.execute_instruction(inst)
        except VentureException as e:
            self.assertEquals(e.exception, 'invalid_constraint')

    def test_predict(self):
        inst = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        val = {'type':'number','value':3}
        o = self.sivm.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)

    def test_configure(self):
        inst = {
                'instruction':'configure',
                "options":{
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
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'forget',
                'directive_id':o1['directive_id'],
                }
        # forget is not implemented
        return
        
        self.sivm.execute_instruction(inst2)

        try:
            self.sivm.execute_instruction(inst2)
        except VentureException as e:
            self.assertEquals(e.exception,'invalid_argument')

    def test_report(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'report',
                'directive_id':o1['directive_id'],
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['value'], {'type':'number','value':3})
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
        # FIXME: Add more comprehensive test for inference parameters once spec stabilizes
        inst = {
                'instruction':'infer',
                'params': {'transitions': 2}
                }
        self.sivm.execute_instruction(inst)

    def test_clear(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'clear',
                }
        o2 = self.sivm.execute_instruction(inst2)
        inst = {
                'instruction':'report',
                'directive_id':o1['directive_id'],
                }
        try:
            self.sivm.execute_instruction(inst)
        except VentureException as e:
            self.assertEquals(e.exception,'invalid_argument')

    def test_rollback(self):
        # engine just segfaults :(
        return
        inst1 = {
                'instruction':'observe',
                'expression': 'aweopfjiaweopfaweopfjopawejiawoiejf',
                'value':{"type":"number","value":3}
                }
        try:
            o1 = self.sivm.execute_instruction(inst1)
        except VentureException as e:
            self.assertEquals(e.exception,'evaluation')
        self.assertEquals(self.sivm.state,'exception')
        inst2 = {
                'instruction':'rollback',
                }
        self.sivm.execute_instruction(inst2)
        self.assertEquals(self.sivm.state,'default')

    def test_get_global_logscore(self):
        # FIXME: not implemented in cxx
        return
        inst1 = {
                'instruction':'observe',
                'expression': ['flip'],
                'value': {"type":"boolean","value":True}
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'get_global_logscore',
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['logscore'],-0.6931471805599453)
    def test_get_logscore(self):
        # FIXME: not implemented in cxx
        return
        inst1 = {
                'instruction':'observe',
                'expression': ['flip'],
                'value': {"type":"boolean","value":True}
                }
        o1 = self.sivm.execute_instruction(inst1)
        inst2 = {
                'instruction':'get_logscore',
                'directive_id':o1['directive_id'],
                }
        o2 = self.sivm.execute_instruction(inst2)
        self.assertEquals(o2['logscore'],-0.6931471805599453)
    
    def test_continuous_inference(self):
        status = {'instruction':'continuous_inference_status'}
        o1 = self.sivm.execute_instruction(status)
        e1 = {'running': False}
        self.assertEquals(o1, e1)
        
        self.sivm.execute_instruction({'instruction':'start_continuous_inference'})
        o2 = self.sivm.execute_instruction(status)
        e2 = {'running': True}
        self.assertEquals(o2, e2)
        
        self.sivm.execute_instruction({'instruction':'stop_continuous_inference'})
        o3 = self.sivm.execute_instruction(status)
        e3 = {'running': False}
        self.assertEquals(o3, e3)
    
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
    
    def test_parse_bool(self):
        v = False
        o = module._parse_value(v)
        e = {"type":"boolean", "value":v}
        self.assertEquals(o, e)

    def test_parse_count(self):        
        v = 0
        o = module._parse_value(v)
        e = {"type":"count", "value":v}
        self.assertEquals(o, e)
        
    def test_parse_number(self):
        v = 0.5
        o = module._parse_value(v)
        e = {"type":"number", "value":v}
        self.assertEquals(o, e)
        
    def test_parse_list(self):
        v = ['l', 'i', 's', 't']
        o = module._parse_value(v)
        e = {"type":"list", "value":v}
        self.assertEquals(o, e)
    
    def test_parse_atom(self):
        v = "a[1]"
        o = module._parse_value(v)
        e = {"type":"atom", "value":1}
        # FIXME: no way parse atoms
        #self.assertEqual(o, e)

if __name__ == '__main__':
    unittest.main()
