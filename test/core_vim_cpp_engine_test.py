import unittest
from venture.vim import CoreVimCppEngine
from venture.exception import VentureException

#Note -- these tests only check for minimum functionality

class TestCoreVimCppEngine(unittest.TestCase):

    def setUp(self):
        self.vim = CoreVimCppEngine()
        self.vim.execute_instruction({"instruction":"clear"})

    def tearDown(self):
        pass

    def test_missing_instruction(self):
        try:
            self.vim.execute_instruction({})
        except VentureException as e:
            self.assertEqual(e.exception,'malformed_instruction')

    def test_missing_argument(self):
        try:
            self.vim.execute_instruction({
                "instruction":"assume",
                "symbol":"MOO"
                })
        except VentureException as e:
            self.assertEqual(e.exception,'missing_argument')
            self.assertEqual(e.data['argument'],'expression')

    def test_invalid_argument(self):
        try:
            self.vim.execute_instruction({
                "instruction":"assume",
                "symbol":"9,d",
                "expression":['a','b',['c']]
                })
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'symbol')

    def test_sanitize_symbol_arg_1(self):
        self.assertEqual(self.vim._sanitize_symbol_arg('add'),'+')
    def test_sanitize_symbol_arg_2(self):
        try:
            self.vim._sanitize_symbol_arg('9ab')
        except VentureException as e:
            self.assertEqual(e.exception, 'invalid_argument')
            self.assertEqual(e.data['argument'], 'symbol')

    def test_sanitize_value_arg_1(self):
        self.assertEqual(self.vim._sanitize_value_arg({
            "type":"real",
            "value":1,
            }),'r[1]')
    def test_sanitize_value_arg_2(self):
        try:
            self.assertEqual(self.vim._sanitize_value_arg({
                "type":"red",
                "value":1,
                }),'red[1]')
        except VentureException as e:
            self.assertEqual(e.exception, 'invalid_argument')
            self.assertEqual(e.data['argument'], 'value')

    def test_sanitize_expression_arg_1(self):
        e = ['a',{'type':'atom','value':1},['b']]
        v = ['a','a[1]',['b']]
        self.assertEqual(self.vim._sanitize_expression_arg(e),v)
    def test_sanitize_expression_arg_2(self):
        try:
            self.vim._sanitize_expression_arg(['a','b',[2]])
        except VentureException as e:
            self.assertEqual(e.exception, 'parse')
            self.assertEqual(e.data['expression_index'], [2,0])

    def test_sanitize_positive_integer_arg_1(self):
        self.assertEqual(self.vim._sanitize_positive_integer_arg(1.0,'moo'),1)
    def test_sanitize_positive_integer_arg_2(self):
        for i in [-1,0,1.3]:
            try:
                self.vim._sanitize_positive_integer_arg(i,'moo')
            except VentureException as e:
                self.assertEqual(e.exception, 'invalid_argument')
                self.assertEqual(e.data['argument'], 'moo')

    def test_sanitize_boolean_arg_1(self):
        self.assertEqual(self.vim._sanitize_boolean_arg(True,'moo'),True)
    def test_sanitize_boolean_arg_2(self):
        try:
            self.vim._sanitize_boolean_arg(1.2,'moo')
        except VentureException as e:
            self.assertEqual(e.exception, 'invalid_argument')
            self.assertEqual(e.data['argument'], 'moo')

    def test_parse_value_1(self):
        v = {"type":"smoothed_count", "value":0.5}
        s = "sc[0.5]"
        self.assertEqual(self.vim._parse_value(s),v)
    def test_parse_value_2(self):
        v = {"type":"number", "value":1.23}
        s = 1.23
        self.assertEqual(self.vim._parse_value(s),v)

    def test_assume(self):
        inst = {
                'instruction':'assume',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'symbol': 'moo'
                }
        val = {'type':'number','value':3}
        o = self.vim.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)

    def test_observe(self):
        inst = {
                'instruction':'observe',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":3}
                }
        o = self.vim.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
    def test_observe_timeout(self):
        return                              # skip this test for the sake of efficiency
        inst = {
                'instruction':'observe',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":4}
                }
        try:
            self.vim.execute_instruction(inst)
        except VentureException as e:
            self.assertIsInstance(e.data['iterations'],(int,float))
            self.assertEquals(e.data['runtime'],5000)

    def test_predict(self):
        inst = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        val = {'type':'number','value':3}
        o = self.vim.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)

    def test_configure(self):
        inst = {
                'instruction':'configure',
                'inference_timeout':5000,           # inference timeout hook is not implemented
                'seed':2,
                }
        o = self.vim.execute_instruction(inst)
        self.assertEquals(o['inference_timeout'],5000)
        self.assertEquals(o['seed'],2)

    def test_forget(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.vim.execute_instruction(inst1)
        inst2 = {
                'instruction':'forget',
                'directive_id':o1['directive_id'],
                }
        self.vim.execute_instruction(inst2)
        try:
            self.vim.execute_instruction(inst2)
        except VentureException as e:
            self.assertEquals(e.exception,'directive_id_not_found')

    def test_report(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.vim.execute_instruction(inst1)
        inst2 = {
                'instruction':'report',
                'directive_id':o1['directive_id'],
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEquals(o2['value'], {'type':'number','value':3})
    def test_report_invalid_did(self):
        inst = {
                'instruction':'report',
                'directive_id':123456,
                }
        try:
            self.vim.execute_instruction(inst)
        except VentureException as e:
            self.assertEquals(e.exception,'directive_id_not_found')

    def test_infer(self):
        inst = {
                'instruction':'infer',
                'iterations':2,
                'resample':True,
                }
        self.vim.execute_instruction(inst)

    def test_clear(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.vim.execute_instruction(inst1)
        inst2 = {
                'instruction':'clear',
                }
        o2 = self.vim.execute_instruction(inst2)
        inst = {
                'instruction':'report',
                'directive_id':o1['directive_id'],
                }
        try:
            self.vim.execute_instruction(inst)
        except VentureException as e:
            self.assertEquals(e.exception,'directive_id_not_found')

    def test_rollback(self):
        inst1 = {
                'instruction':'observe',
                #'expression': 'add',                       #NOTE: this causes segfault
                'expression': 'aweopfjiaweopfaweopfjopawejiawoiejf',
                'value':{"type":"number","value":3}
                }
        try:
            o1 = self.vim.execute_instruction(inst1)
        except VentureException as e:
            self.assertEquals(e.exception,'evaluation')
        self.assertEquals(self.vim.state,'exception')
        inst2 = {
                'instruction':'rollback',
                }
        self.vim.execute_instruction(inst2)
        self.assertEquals(self.vim.state,'default')

    def test_get_global_logscore(self):
        inst1 = {
                'instruction':'observe',
                'expression': ['flip'],
                'value': {"type":"boolean","value":True}
                }
        o1 = self.vim.execute_instruction(inst1)
        inst2 = {
                'instruction':'get_global_logscore',
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEquals(o2['logscore'],-0.6931471805599453)

if __name__ == '__main__':
    unittest.main()
