import unittest
from venture.vim import CoreVimCppEngine, VentureVim
import venture.vim.venture_vim as module
from venture.exception import VentureException

#Note -- these tests only check for minimum functionality
# these tests alfo depend on a functional CoreVimCppEngine

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

if __name__ == '__main__':
    unittest.main()
