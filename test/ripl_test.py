import unittest
from venture.ripl import Ripl
from venture.exception import VentureException
from venture.sivm import VentureSivm, CoreSivmCppEngine
from venture.parser import ChurchPrimeParser, VentureScriptParser

class TestRipl(unittest.TestCase):
    def setUp(self):
        self.core_sivm = CoreSivmCppEngine()
        self.core_sivm.execute_instruction({"instruction":"clear"})
        self.venture_sivm = VentureSivm(self.core_sivm)
        parser1 = ChurchPrimeParser()
        parser2 = VentureScriptParser()
        self.ripl = Ripl(self.venture_sivm,
                {"church_prime":parser1,
                    "church_prime_2":parser1,
                    "venture_script":parser2})
        self.ripl.set_mode('church_prime')

    ############################################
    # Languages
    ############################################

    def test_modes(self):
        output = self.ripl.list_available_modes()
        self.assertEqual(set(output),set(['church_prime','church_prime_2','venture_script']))
        self.ripl.set_mode('church_prime')
        output = self.ripl.get_mode()
        self.assertEqual(output,'church_prime')
        self.ripl.set_mode('church_prime_2')
        output = self.ripl.get_mode()
        self.assertEqual(output,'church_prime_2')
        with self.assertRaises(VentureException):
            self.ripl.set_mode("moo")

    ############################################
    # Execution
    ############################################

    def test_execute_instruction(self):
        f = self.ripl.execute_instruction
        f("[assume a 1]")
        f("[assume b (+ 1 2)]")
        f("[assume c (- b a)]")
        ret_value= f("[predict c]")
        self.assertEqual(ret_value['value'], {"type":"number","value":2})

    def test_execute_program(self):
        f = self.ripl.execute_program
        ret_value = f("[assume a 1] [assume b (+ 1 2)] [assume c (- b a)] [predict c]")
        self.assertEqual(ret_value[-1]['value'], {"type":"number","value":2})

    def test_parse_exception_sugaring(self):
        f = self.ripl.execute_instruction
        try:
            f("[assume a (+ (if 1 2) 3)]")
        except VentureException as e:
            self.assertEqual(e.data['text_index'], [13,20])
            self.assertEqual(e.exception, 'parse')

    def test_invalid_argument_exception_sugaring(self):
        f = self.ripl.execute_instruction
        try:
            f("[forget moo]")
        except VentureException as e:
            self.assertEqual(e.data['text_index'], [8,10])
            self.assertEqual(e.exception, 'invalid_argument')

    ############################################
    # Text manipulation
    ############################################

    def test_substitute_params(self):
        string = "a %s %j %v"
        params = ['b','2',2]
        expected_output = 'a b "2" 2'
        output = self.ripl.substitute_params(string,params)
        self.assertEqual(output, expected_output)

    def test_split_program(self):
        output = self.ripl.split_program(" [ force blah count<132>][ infer 132 ]")
        instructions = ['[ force blah count<132>]','[ infer 132 ]']
        indices = [[1,24],[25,37]]
        self.assertEqual(output,[instructions, indices])

    def test_get_text(self):
        self.ripl.set_mode('church_prime')
        text = "[assume a (+ (if true 2 3) 4)]"
        value = self.ripl.execute_instruction(text)
        output = self.ripl.get_text(value['directive_id'])
        self.assertEqual(output, ['church_prime',text])

    def test_character_index_to_expression_index(self):
        text = "[assume a (+ (if true 2 3) 4)]"
        value = self.ripl.execute_instruction(text)
        output = self.ripl.character_index_to_expression_index(value['directive_id'], 10)
        self.assertEqual(output, [])

    def test_expression_index_to_text_index(self):
        text = "[assume a (+ (if true 2 3) 4)]"
        value = self.ripl.execute_instruction(text)
        output = self.ripl.expression_index_to_text_index(value['directive_id'], [])
        self.assertEqual(output, [10,28])


    ############################################
    # Directives
    ############################################

    def test_assume(self):
        #normal assume
        ret_value = self.ripl.assume('c', '(+ 1 1)')
        self.assertEqual(ret_value['value']['value'], 2)
        #labeled assume
        ret_value = self.ripl.assume('d', '(+ 1 1)', 'moo')
        self.assertEqual(ret_value['value']['value'], 2)

    def test_predict(self):
        #normal predict
        ret_value = self.ripl.predict('(+ 1 1)')
        self.assertEqual(ret_value['value']['value'], 2)
        #labeled predict
        ret_value = self.ripl.predict('(+ 1 1)','moo')
        self.assertEqual(ret_value['value']['value'], 2)

    def test_observe(self):
        #normal observe
        self.ripl.assume('a','(uniform_continuous 0 1)')
        self.ripl.observe('a',0.5)
        output = self.ripl.predict('a')
        self.assertEqual(output['value']['value'], 0.5)
        #labeled observe
        self.ripl.observe('true','true','moo')


    ############################################
    # Core
    ############################################

    def test_configure(self):
        ret_value = self.ripl.configure({"seed":123,"inference_timeout":5000})
        self.assertEqual(ret_value, {"seed":123, "inference_timeout":5000})

    def test_forget(self):
        #normal forget
        ret_value = self.ripl.execute_instruction('[ assume a (uniform_continuous 0 1) ]')
        self.ripl.forget(ret_value['directive_id'])
        #labeled forget
        self.ripl.assume('a','(uniform_continuous 0 1)', 'moo')
        self.ripl.forget('moo')
        with self.assertRaises(VentureException):
            self.ripl.forget('moo')

    def test_report(self):
        #normal report
        ret_value = self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        output = self.ripl.report(ret_value['directive_id'])
        self.assertEqual(output,1)
        #labeled report
        output = self.ripl.report('moo')
        self.assertEqual(output,1)

    def test_infer(self):
        ret_value = self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        self.ripl.infer(1)
        self.ripl.infer(1,True)

    def test_clear(self):
        ret_value = self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        self.ripl.report('moo')
        self.ripl.clear()
        with self.assertRaises(VentureException):
            self.ripl.report('moo')

    def test_rollback(self):
        #TODO: write test after exception states are implemented
        pass

    def test_list_directives(self):
        self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        output = self.ripl.list_directives()
        self.assertEqual(len(output),1)

    def test_get_directive(self):
        ret_value = self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        output = self.ripl.get_directive(ret_value['directive_id'])
        self.assertEqual(output['directive_id'],output['directive_id'])

    def test_force(self):
        #normal force
        self.ripl.assume('a','(uniform_continuous 0 1)')
        self.ripl.force('a',0.2)
        self.ripl.force('a',0.5)
        output = self.ripl.predict('a')
        self.assertEqual(output['value']['value'], 0.5)

    def test_sample(self):
        #normal force
        output = self.ripl.sample('(+ 1 1)')
        self.assertEqual(output, 2)

    def test_continuous_inference_configure(self):
        #normal force
        options = {
                "continuous_inference_enable":True
                }
        output = self.ripl.continuous_inference_configure(options)
        self.assertEqual(output, options)

    def test_continuous_inference_enable_disable(self):
        self.ripl.continuous_inference_enable()
        output = self.ripl.continuous_inference_configure()['continuous_inference_enable']
        self.assertEqual(output, True)
        self.ripl.continuous_inference_disable()
        output = self.ripl.continuous_inference_configure()['continuous_inference_enable']
        self.assertEqual(output, False)

    def test_get_current_exception(self):
        #TODO: write test after exception states are implemented
        pass

    def test_get_state(self):
        output = self.ripl.get_state()
        self.assertEqual(output,'default')

    def test_get_logscore(self):
        #TODO: fix test after get_logscore is implemented
        return
        ret_value = self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        output = self.ripl.get_logscore(ret_value['directive_id'])
        self.assertEqual(output,0)
        output = self.ripl.get_logscore('moo')
        self.assertEqual(output,0)

    def test_get_global_logscore(self):
        self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        output = self.ripl.get_global_logscore()
        self.assertEqual(output,0)

if __name__ == '__main__':
    unittest.main()
