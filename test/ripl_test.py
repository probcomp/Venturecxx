import unittest
from venture.ripl import Ripl
from venture.exception import VentureException
from venture.vim import VentureVim, CoreVimCppEngine
from venture.parser import VentureLispParser

class TestRipl(unittest.TestCase):
    def setUp(self):
        self.core_vim = CoreVimCppEngine()
        self.core_vim.execute_instruction({"instruction":"clear"})
        self.venture_vim = VentureVim(self.core_vim)
        self.parser = VentureLispParser()
        self.ripl = Ripl(self.venture_vim,
                {"venture_lisp":self.parser,
                    "venture_lisp_2":self.parser})

    def test_modes(self):
        output = self.ripl.list_available_modes()
        self.assertEqual(set(output),set(['venture_lisp','venture_lisp_2']))
        self.ripl.set_mode('venture_lisp')
        output = self.ripl.get_mode()
        self.assertEqual(output,'venture_lisp')
        self.ripl.set_mode('venture_lisp_2')
        output = self.ripl.get_mode()
        self.assertEqual(output,'venture_lisp_2')
        with self.assertRaises(VentureException):
            self.ripl.set_mode("moo")

    def test_execute_instruction(self):
        f = self.ripl.execute_instruction
        f("assume a = 1")
        f("assume b = (+ 1 2)")
        f("assume c = (- b a)")
        text_index, ret_value= f("predict c")
        self.assertEqual(ret_value['value'], {"type":"number","value":2})

    def test_parse_exception_sugaring(self):
        f = self.ripl.execute_instruction
        try:
            f("assume a = (+ (if 1 2) 3)")
        except VentureException as e:
            self.assertEqual(e.data['text_index'], [14,21])
            self.assertEqual(e.exception, 'parse')

    def test_invalid_argument_exception_sugaring(self):
        f = self.ripl.execute_instruction
        try:
            f("forget moo")
        except VentureException as e:
            self.assertEqual(e.data['text_index'], [7,9])
            self.assertEqual(e.exception, 'invalid_argument')



if __name__ == '__main__':
    unittest.main()
