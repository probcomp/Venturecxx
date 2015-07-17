# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest
from nose.plugins.attrib import attr

from venture.exception import VentureException
from venture.parser import ChurchPrimeParser
from venture.test.test_helpers import ParserTestCase
import venture.value.dicts as v

# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestChurchPrimeParser(unittest.TestCase):
    _multiprocess_can_split_ = True
    def setUp(self):
        self.p = ChurchPrimeParser.instance()
        self.expression = None

    def test_expression(self):
        with self.assertRaises(VentureException):
            self.p.parse_locexpression("")
        self.assertEqual(self.p.parse_locexpression("(a b (c real<1>))"),
                {'loc': [0,16], 'value':[
                    {'loc': [1,1], 'value': v.sym('a')},
                    {'loc': [3,3], 'value': v.sym('b')},
                    {'loc': [5,15], 'value': [
                        {'loc': [6,6], 'value': v.sym('c')},
                        {'loc': [8,14], 'value': v.real(1.0)}]}]})

    def test_parse_instruction(self):
        output = self.p.parse_instruction('[assume a (b c d)]')
        expected = {'instruction':'assume', 'symbol':v.sym('a'),
                    'expression':[v.sym('b'),v.sym('c'),v.sym('d')]}
        self.assertEqual(output,expected)

    def test_parse_and_unparse_instruction(self):
        for instruction in ["[assume a (b c d)]", "foo: [assume a (b c d)]"]:
            self.assertEqual(self.p.unparse_instruction(self.p.parse_instruction(instruction)), instruction)

    # detects bug where '>=' is parsed as '> =' (because '>' is its own symbol)
    def test_double_symbol(self):
        output = self.p.parse_instruction('[predict (>= 1 1)]')
        expected = {
            'expression': [v.symbol('gte'), v.number(1.0), v.number(1.0)],
            'instruction': 'predict'}
        self.assertEqual(output, expected)

    # detects bug parsing lambda expressions with no arguments
    def test_empty_lambda(self):
        output = self.p.parse_instruction('[predict (lambda () 0)]')
        expected = {'instruction': 'predict',
                    'expression': [v.symbol('lambda'), [], v.number(0.0)]}
        self.assertEqual(output, expected)

    def test_split_program(self):
        # FIXME: this test should pass, but should be revised since infer has changed
        output = self.p.split_program(" [ force blah count<132>][ infer 132 ]")
        instructions = ['[ force blah count<132>]','[ infer 132 ]']
        indices = [[1,24],[25,37]]
        self.assertEqual(output,[instructions, indices])

    def test_split_instruction(self):
        output = self.p.split_instruction(" [force blah count<132> ]")
        indices = {
                "instruction": [2,6],
                "expression": [8,11],
                "value": [13,22],
                }
        strings = {
                "instruction": "force",
                "expression": "blah",
                "value": "count<132>",
                }
        self.assertEqual(output,[strings,indices])

    def test_expression_index_to_text_index(self):
        s = "(a b (c (d e) f ))"
        f = self.p.expression_index_to_text_index
        output = f(s, [0])
        self.assertEqual(output, [1,1])
        output = f(s, [2])
        self.assertEqual(output, [5,16])
        output = f(s, [2,0])
        self.assertEqual(output, [6,6])
        output = f(s, [2,1,1])
        self.assertEqual(output, [11,11])


    def test_character_index_to_expression_index(self):
        s = "(a b (c (d e) f ))"
        f = self.p.character_index_to_expression_index
        output = f(s, 0)
        self.assertEqual(output, [])
        output = f(s, 1)
        self.assertEqual(output, [0])
        output = f(s, 2)
        self.assertEqual(output, [])
        output = f(s, 5)
        self.assertEqual(output, [2])
        output = f(s, 6)
        self.assertEqual(output, [2,0])

    def test_get_instruction_string(self):
        f = self.p.get_instruction_string
        output = f('observe')
        self.assertEqual(output,'[ observe %(expression)s %(value)v ]')
        output = f('infer')
        self.assertEqual(output,'[ infer %(expression)s ]')

    def test_mark_up_expression_smoke(self):
        parsed = self.p.parse_expression("(add 2 3)")
        def red(string):
            return "\x1b[31m" + string + "\x1b[39;49m"
        def green(string):
            return "\x1b[32m" + string + "\x1b[39;49m"
        marked = self.p.unparse_expression_and_mark_up(parsed, [([0], red), ([1], green)])
        # The junk in the answer is ANSI terminal color codes
        self.assertEqual('(\x1b[31madd\x1b[39;49m \x1b[32m2\x1b[39;49m 3)', marked)

    def test_string(self):
        output = self.p.parse_expression('"foo"')
        expected = v.string('foo')
        self.assertEqual(output,expected)
