import unittest
from venture.ripl import Ripl
from venture.exception import VentureException
from venture.sivm import VentureSIVM, CoreSIVMCppEngine
from venture.parser import ChurchPrimeParser

class TestRipl(unittest.TestCase):
    def setUp(self):
        self.core_sivm = CoreSIVMCppEngine()
        self.core_sivm.execute_instruction({"instruction":"clear"})
        self.venture_sivm = VentureSIVM(self.core_sivm)
        self.parser = ChurchPrimeParser()
        self.ripl = Ripl(self.venture_sivm,
                {"church_prime":self.parser,
                    "church_prime_2":self.parser})

    def test_modes(self):
        output = self.ripl.list_available_modes()
        self.assertEqual(set(output),set(['church_prime','church_prime_2']))
        self.ripl.set_mode('church_prime')
        output = self.ripl.get_mode()
        self.assertEqual(output,'church_prime')
        self.ripl.set_mode('church_prime_2')
        output = self.ripl.get_mode()
        self.assertEqual(output,'church_prime_2')
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