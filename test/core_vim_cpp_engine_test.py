import unittest
from venture.vim import CoreVimCppEngine
from venture.exception import VentureException

#Note -- these tests only check for minimum functionality

class TestCoreVimCppEngine(unittest.TestCase):

    def setUp(self):
        self.vim = CoreVimCppEngine()

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

    def test_parse_value_1(self):
        v = {"type":"smoothed_count", "value":0.5}
        s = "sc[0.5]"
        self.assertEqual(self.vim._parse_value(s),v)

    def test_assume(self):
        inst = {
                'instruction':'assume',
                'expression': ['add',{'type':'number','value':1},{'type':'number','value':2}],
                'symbol': 'moo'
                }
        o = {'directive_id':1, 'value':{'type':'number','value':3}}
        self.assertEqual(self.vim.execute_instruction(inst),o)


if __name__ == '__main__':
    unittest.main()
