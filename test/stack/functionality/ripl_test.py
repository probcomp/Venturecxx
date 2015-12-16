# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.
import unittest

from nose.plugins.attrib import attr

from venture.exception import VentureException
from venture.parser import ChurchPrimeParser
from venture.parser import VentureScriptParser
from venture.ripl import Ripl
from venture.sivm import VentureSivm
from venture.test.config import get_core_sivm
import venture.value.dicts as v

# TODO Not really backend independent, but doesn't test the backend much.
# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestRipl(unittest.TestCase):
    _multiprocess_can_split_ = True

    def setUp(self):
        self.core_sivm = get_core_sivm()
        self.core_sivm.execute_instruction({"instruction":"clear"})
        self.venture_sivm = VentureSivm(self.core_sivm)
        parser1 = ChurchPrimeParser.instance()
        parser2 = VentureScriptParser.instance()
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
        self.assertEqual(ret_value['value'], v.number(2))

    def test_execute_program(self):
        f = self.ripl.execute_program
        ret_value = f("[assume a 1] [assume b (+ 1 2)] [assume c (- b a)] [predict c]")
        self.assertEqual(ret_value[-1]['value'], v.number(2))

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
        self.assertEqual(ret_value, 2)
        #labeled assume
        ret_value = self.ripl.assume('d', '(+ 1 1)', 'moo')
        self.assertEqual(ret_value, 2)

    def test_predict(self):
        #normal predict
        ret_value = self.ripl.predict('(+ 1 1)')
        self.assertEqual(ret_value, 2)
        #labeled predict
        ret_value = self.ripl.predict('(+ 1 1)','moo')
        self.assertEqual(ret_value, 2)

    def test_observe(self):
        #normal observe
        self.ripl.assume('a','(uniform_continuous 0 1)')
        a = self.ripl.sample('a')
        weights = self.ripl.observe('a', 0.5)
        # TODO test for when auto-incorporation is disabled
        self.assertEqual(self.ripl.sample('a'), 0.5)
        self.assertEqual(weights, [0])

    def test_labeled_observe(self):
        #labeled observe
        self.ripl.assume('b','(uniform_continuous 0 1)')
        b = self.ripl.sample('b')
        weights = self.ripl.observe('b', 0.5, 'moo')
        # TODO test for when auto-incorporation is disabled
        self.assertEqual(self.ripl.sample('b'), 0.5)
        self.assertEqual(weights, [0])

    ############################################
    # Core
    ############################################

    def test_configure(self):
        ret_value = self.ripl.configure({"seed":0,"inference_timeout":5000})
        self.assertEqual(ret_value, {"seed":0, "inference_timeout":5000})

    def test_forget(self):
        #normal forget
        ret_value = self.ripl.execute_instruction('[ predict (uniform_continuous 0 1) ]')
        weights = self.ripl.forget(ret_value['directive_id'])
        self.assertEqual(weights, [0])
        with self.assertRaises(VentureException):
            self.ripl.forget(ret_value['directive_id'])
        #labeled forget
        self.ripl.assume('a','(uniform_continuous 0 1)', 'moo')
        # assumes can be forgotten
        weights = self.ripl.forget('moo')
        self.assertEqual(weights, [0])
        # observes can be forgotten
        self.ripl.observe('(uniform_continuous 0 (exp 1))', 2, 'baa')
        weights = self.ripl.forget('baa')
        self.assertEqual(weights, [-1])

    def test_report(self):
        #normal report
        ret_value = self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        output = self.ripl.report(ret_value['directive_id'])
        self.assertEqual(output,1)
        #labeled report
        output = self.ripl.report('moo')
        self.assertEqual(output,1)

    def test_infer(self):
        # FIXME: Should test multiple kernels and other infer parameters here
        self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        self.ripl.infer(1)

    def test_clear(self):
        self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        self.ripl.report('moo')
        self.ripl.clear()
        with self.assertRaises(VentureException):
            self.ripl.report('moo')

    def test_rollback(self):
        #TODO: write test after exception states are implemented
        pass

    def test_list_directives(self):
        n_before = len(self.ripl.list_directives())
        self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        n_after = len(self.ripl.list_directives())
        self.assertEqual(n_after, n_before + 1)

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
        self.assertEqual(output, 0.5)

    def test_sample(self):
        #normal force
        output = self.ripl.sample('(+ 1 1)')
        self.assertEqual(output, 2)

    def test_get_current_exception(self):
        # TODO: write test after exception states are implemented
        pass

    def test_get_state(self):
        output = self.ripl.get_state()
        self.assertEqual(output,'default')

    def test_get_global_logscore(self):
        self.ripl.execute_instruction('moo : [ assume a (+ 0 1) ]')
        output = self.ripl.get_global_logscore()
        self.assertEqual(output,0)

    ############################################
    # Profiler
    ############################################

    def test_profiler_configure(self):
        output = self.ripl.profiler_configure()
        self.assertEqual(output, {'profiler_enabled': False})
        output = self.ripl.profiler_configure({'profiler_enabled': True})
        self.assertEqual(output, {'profiler_enabled': True})
        output = self.ripl.profiler_configure({'profiler_enabled': False})
        self.assertEqual(output, {'profiler_enabled': False})

