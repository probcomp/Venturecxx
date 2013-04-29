import unittest
from venture.vim import CoreVimCppEngine, VentureVim
import venture.vim.venture_vim as module
from venture.exception import VentureException

#Note -- these tests only check for minimum functionality
# these tests also depend on a functional CoreVimCppEngine

class TestVentureVim(unittest.TestCase):

    def setUp(self):
        self.core_vim = CoreVimCppEngine()
        self.core_vim.execute_instruction({"instruction":"clear"})
        self.vim = VentureVim(self.core_vim)

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
    def test_invalid_label(self):
        inst = {
                'instruction':'labeled_assume',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'symbol': 'moo',
                'label': '123moo'
                }
        try:
            self.vim.execute_instruction(inst)
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
        self.vim.execute_instruction(inst)
        try:
            self.vim.execute_instruction(inst)
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'label')



    # test expression desugaring and exception sugaring
    def test_sugaring_1(self):
        #stub the VIM
        def f(expression):
            raise VentureException('parse', 'moo', expression_index=[0,3,2,0,1,0])
        self.core_vim.execute_instruction = f
        try:
            self.vim.execute_instruction({
                "instruction":"assume",
                "symbol":"d",
                "expression":['if','a','b',['let',[['c','d']],'e']]
                })
        except VentureException as e:
            self.assertEqual(e.exception,'parse')
            self.assertEqual(e.data['expression_index'],[3,1,0,0])
    # test exception_index desugaring
    def test_sugaring_2(self):
        num = {'type':'number','value':1}
        did = self.vim.execute_instruction({
            "instruction":"assume",
            "symbol":"d",
            "expression":['if',num,num,['let',[['a',num]],num]]
            })['directive_id']
        #stub the VIM
        def f(expression):
            got = expression['source_code_location']['expression_index']
            expected = [0,3,2,0,1,0]
            self.assertEqual(got,expected)
            return {"breakpoint_id":14}
        self.core_vim.execute_instruction = f
        self.vim.execute_instruction({
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
        o = self.vim.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)
    def test_labeled_observe(self):
        inst = {
                'instruction':'labeled_observe',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":3},
                'label' : 'moo'
                }
        o = self.vim.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
    def test_labeled_predict(self):
        inst = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label' : 'moo'
                }
        val = {'type':'number','value':3}
        o = self.vim.execute_instruction(inst)
        self.assertIsInstance(o['directive_id'],(int,float))
        self.assertEquals(o['value'],val)
    def test_labeled_forget(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label' : 'moo',
                }
        o1 = self.vim.execute_instruction(inst1)
        inst2 = {
                'instruction':'labeled_forget',
                'label' : 'moo',
                }
        self.vim.execute_instruction(inst2)
        try:
            self.vim.execute_instruction(inst2)
        except VentureException as e:
            self.assertEquals(e.exception,'invalid_argument')
        inst3 = {
                'instruction':'list_directives',
                }
        o3 = self.vim.execute_instruction(inst3)
        self.assertEquals(o3['directives'], [])
    def test_labeled_report(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label' : 'moo',
                }
        o1 = self.vim.execute_instruction(inst1)
        inst2 = {
                'instruction':'labeled_report',
                'label' : 'moo',
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEquals(o2['value'], {'type':'number','value':3})
    def test_labeled_get_logscore(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label' : 'moo',
                }
        o1 = self.vim.execute_instruction(inst1)
        inst2 = {
                'instruction':'labeled_get_logscore',
                'label' : 'moo',
                }
        o2 = self.vim.execute_instruction(inst2)
        # not implemented in current implementation
        # self.assertEquals(o2['logscore'],-0.6931471805599453)
    def test_list_directives(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.vim.execute_instruction(inst1)
        inst1['directive_id'] = o1['directive_id']
        inst2 = {
                'instruction':'list_directives',
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEquals(o2['directives'], [inst1])
    def test_get_directive(self):
        inst1 = {
                'instruction':'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        o1 = self.vim.execute_instruction(inst1)
        inst1['directive_id'] = o1['directive_id']
        inst2 = {
                'instruction':'get_directive',
                'directive_id':o1['directive_id'],
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEquals(o2['directive'], inst1)
    def test_labeled_get_directive(self):
        inst1 = {
                'instruction':'labeled_predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'label': 'moo',
                }
        o1 = self.vim.execute_instruction(inst1)
        del inst1['label']
        inst2 = {
                'instruction':'labeled_get_directive',
                'label': 'moo',
                }
        o2 = self.vim.execute_instruction(inst2)
        output = {
                'directive_id': o1['directive_id'],
                'instruction': 'predict',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        self.assertEquals(o2['directive'], output)
    def test_force(self):
        inst = {
                'instruction':'force',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":3}
                }
        o = self.vim.execute_instruction(inst)
        inst2 = {
                'instruction':'list_directives',
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEquals(o2['directives'], [])
    def test_sample(self):
        inst = {
                'instruction':'sample',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                }
        val = {'type':'number','value':3}
        o = self.vim.execute_instruction(inst)
        self.assertEquals(o['value'],val)
        inst2 = {
                'instruction':'list_directives',
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEquals(o2['directives'], [])
    def test_continuous_inference_config(self):
        inst1 = {
                'instruction':'continuous_inference_config',
                }
        o1 = self.vim.execute_instruction(inst1)
        e1 = {
                'enable_continuous_inference': False,
                }
        self.assertEquals(o1, e1)
        inst2 = {
                'instruction':'continuous_inference_config',
                'enable_continuous_inference': True,
                }
        o2 = self.vim.execute_instruction(inst2)
        e2 = {
                'enable_continuous_inference': True,
                }
        self.assertEquals(o2, e2)
    def test_get_current_exception(self):
        inst1 = {
                'instruction':'force',
                'expression': ['moo',{'type':'number','value':1},{'type':'number','value':2}],
                'value': {"type":"real","value":3}
                }
        try:
            o1 = self.vim.execute_instruction(inst1)
        except VentureException as e:
            pass
        inst2 = {
                'instruction':'get_current_exception',
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEqual(o2['exception']['exception'], 'evaluation')
    def test_get_state(self):
        inst1 = {
                'instruction':'get_state',
                }
        o1 = self.vim.execute_instruction(inst1)
        self.assertEqual(o1['state'], 'default')
    def test_debugger_list_breakpoints_and_debugger_get_breakpoint(self):
        #stub the VIM
        def f(expression):
            return {"breakpoint_id":14}
        self.core_vim.execute_instruction = f
        inst1 = {
            "instruction":"debugger_set_breakpoint_address",
            "address": "fefefefefefefe",
            }
        o1 = self.vim.execute_instruction(inst1)
        del inst1['instruction']
        inst1['breakpoint_id'] = o1['breakpoint_id']
        inst2 = {
                'instruction' : 'debugger_list_breakpoints',
                }
        o2 = self.vim.execute_instruction(inst2)
        self.assertEqual(o2['breakpoints'], [inst1])
        inst3 = {
                'instruction' : 'debugger_get_breakpoint',
                'breakpoint_id' : o1['breakpoint_id'],
                }
        o3 = self.vim.execute_instruction(inst3)
        self.assertEqual(o3['breakpoint'], inst1)



if __name__ == '__main__':
    unittest.main()
