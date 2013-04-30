#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import unittest
from venture.exception import VentureException
from venture.parser import VentureLispParser
from venture.test.test_helpers import ParserTestCase


class TestVentureLispParser(ParserTestCase):
    def setUp(self):
        self.p = VentureLispParser()

    def test_expression(self):
        self.expression = self.p.expression
        self.run_test( "",
                None)
        self.run_test( "()",
                None)
        self.run_test( "(a b (c real<1>))",
                [['a','b',['c',{"type":"real","value":1.0}]]])

    def test_parse_value(self):
        output = self.p.parse_value('1')
        expected = {'type':'number','value':1.0}
        self.assertEqual(output,expected)

    def test_parse_expression(self):
        output = self.p.parse_expression('(a b c)')
        expected = ['a','b','c']
        self.assertEqual(output,expected)

    def test_parse_symbol(self):
        output = self.p.parse_symbol('+')
        expected = 'add'
        self.assertEqual(output,expected)

    def test_parse_instruction(self):
        output = self.p.parse_instruction('assume a = (b c d)')
        expected = {'instruction':'assume', 'symbol':'a', 'expression':['b','c','d']}
        self.assertEqual(output,expected)

    def test_split_program(self):
        output = self.p.split_program(" force blah = count<132> infer 132")
        instructions = [{
                    "instruction" : "force",
                    "expression" : "blah",
                    "value" : {'type':'count', 'value':132.0},
                    },{
                    "instruction" : "infer",
                    "iterations" : 132,
                    "resample" : False,
                    }]
        indices = [1,25]
        self.assertEqual(output,(instructions, indices))

    def test_get_text_index(self):
        pass





if __name__ == '__main__':
    unittest.main()
