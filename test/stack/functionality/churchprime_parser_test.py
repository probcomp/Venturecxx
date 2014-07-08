# Copyright (c) 2013, MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from venture.parser import ChurchPrimeParser
from venture.test.test_helpers import ParserTestCase


class TestChurchPrimeParser(ParserTestCase):
    _multiprocess_can_split_ = True
    def setUp(self):
        self.p = ChurchPrimeParser.instance()
        self.expression = None

    def test_expression(self):
        self.expression = self.p.expression
        self.run_test( "",
                None)
        #self.run_test( "()",
        #        None)
        self.run_test( "(a b (c real<1>))",
                [{'loc': [0,16], 'value':[
                    {'loc': [1,1], 'value': 'a'},
                    {'loc': [3,3], 'value': 'b'},
                    {'loc': [5,15], 'value': [
                        {'loc': [6,6], 'value': 'c'},
                        {'loc': [8,14], 'value': {'type': 'real', 'value': 1.0}}]}]}])

    def test_parse_instruction(self):
        output = self.p.parse_instruction('[assume a (b c d)]')
        expected = {'instruction':'assume', 'symbol':'a', 'expression':['b','c','d']}
        self.assertEqual(output,expected)
    
    # detects bug where '>=' is parsed as '> =' (because '>' is its own symbol)
    def test_double_symbol(self):
        output = self.p.parse_instruction('[predict (>= 1 1)]')
        expected = {
            'expression':
                ['gte',
                    {'type': 'number', 'value': 1.0},
                    {'type': 'number', 'value': 1.0}],
            'instruction': 'predict'}
        self.assertEqual(output, expected)
    
    # detects bug parsing lambda expressions with no arguments
    def test_empty_lambda(self):
        output = self.p.parse_instruction('[predict (lambda () 0)]')
        expected = {'instruction': 'predict',
            'expression': ['lambda', [], {'type': 'number', 'value': 0.0}]}
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


