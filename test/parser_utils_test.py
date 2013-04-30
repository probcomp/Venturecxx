#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import unittest
from venture.exception import VentureException
from venture.parser import utils
from venture.test.test_helpers import ParserTestCase

import time
import sys
import traceback
import StringIO


class TestParserUtilsAtoms(ParserTestCase):
    def setUp(self):
        pass

    def test_symbol(self):
        # Symbol
        #
        self.expression = utils.symbol_token(blacklist_symbols = ['lambda', 'if'],
                whitelist_symbols=['+'], symbol_map={'+':'add'})
        self.run_test( "",
                None)
        self.run_test( "3",
                None)
        self.run_test( "+",
                ['add'])
        self.run_test( "lambda",
                None)
        self.run_test( "if",
                None)
        self.run_test( "awef123",
                ["awef123"])
        self.run_test( r'awe!@#e',
                None)

    def test_number(self):
        # Number
        #
        self.expression = utils.number_token()
        self.run_test( "",
                None)
        self.run_test( "3",
                [3.0])
        self.run_test( "-3.22",
                [-3.22])
        self.run_test( "3.",
                [3.0])
        self.run_test( "-.3",
                [-.3])
        self.run_test( "moo",
                None)

    def test_integer(self): 
        # Integer
        #
        self.expression = utils.integer_token()
        self.run_test( "",
                None)
        self.run_test( "3",
                [3])
        self.run_test( "moo",
                None)


    def test_string(self):
        # String
        #
        self.expression = utils.string_token()
        self.run_test( r'',
                None)
        self.run_test( r'"abc"',
                [r'abc'])
        self.run_test( r'"\""',
                [r'"'])
        self.run_test( r'"\n"',
                ['\n'])
        self.run_test( r'"\t"',
                ['\t'])
        self.run_test( r'"\f"',
                ['\f'])
        self.run_test( r'"\062"',
                ['2'])
        self.run_test( r'"\462"',
                None)
   
    def test_null(self):
        # Null
        #
        self.expression = utils.null_token()
        self.run_test( "",
                None)
        self.run_test( "null",
                [None])

    def test_boolean(self):
        # Boolean
        #
        self.expression = utils.boolean_token()
        self.run_test( "",
                None)
        self.run_test( "true",
                [True])
        self.run_test( "false",
                [False])

    def test_json_value(self):
        # Json value
        #
        self.expression = utils.json_value_token()
        self.run_test( "",
                None)
        self.run_test( r'"abc"',
                [r'abc'])
        self.run_test( r'2.3',
                [2.3])
        self.run_test( "null",
                [None])
        self.run_test( "true",
                [True])
        self.run_test( "[1,2,[3,[]]]",
                [[1,2,[3,[]]]])
        self.run_test( '{"a":{"b":{}}}',
                [{"a":{"b":{}}}])

    def test_value(self):
        # Value
        #
        self.expression = utils.value_token()
        self.run_test( "",
                None)
        self.run_test( "boolean<true>",
                None)
        self.run_test( "number<1.0>",
                None)
        self.run_test( "real<1.0>",
                [{"type": "real", "value":1.0}])
        self.run_test( 'url<"www.google.com">',
                [{"type": "url", "value":"www.google.com"}])
        self.run_test( 'simplex_point<[0.5,0.5]>',
                [{"type": "simplex_point", "value":[0.5,0.5]}])
        self.run_test( 'costume<{"hat_color":"blue","shirt_color":"red"}>',
                [{"type": "costume", "value":
                    {"hat_color":"blue", "shirt_color":"red"}}])


    def test_number_literal(self):
        # Number Literal
        #
        self.expression = utils.number_literal_token()
        self.run_test( "",
                None)
        self.run_test( "1",
                [{"type":"number", "value":1.0}])


    def test_boolean_literal(self):
        # Boolean Literal
        #
        self.expression = utils.boolean_literal_token()
        self.run_test( "",
                None)
        self.run_test( "true",
                [{"type":"boolean", "value":True}])


    def test_literal_token(self):
        # Literal
        #
        self.expression = utils.literal_token()
        self.run_test( "",
                None)
        self.run_test( "1",
                [{"type":"number", "value":1.0}])
        self.run_test( "true",
                [{"type":"boolean", "value":True}])
        self.run_test( "real<1.0>",
                [{"type": "real", "value":1.0}])













class TestParserUtilsInstructions(ParserTestCase):
    def setUp(self):
        symbol = utils.symbol_token()
        value = utils.literal_token()
        expression = utils.symbol_token()   #for simplicity
        self.instruction, self.program = utils.init_instructions(value, symbol, expression)
        self.expression = self.instruction


    def test_assume(self):
        # Assume
        #
        self.run_test( "",
                None)
        self.run_test( "assuMe blah = moo",
                [{
                    "instruction" : "assume",
                    "symbol" : "blah",
                    "expression" : "moo"
                    }])
    
    def test_labeled_assume(self):
        self.run_test( "name : assume a = b",
                [{
                    "instruction" : "labeled_assume",
                    "symbol" : "a",
                    "expression" : "b",
                    "label" : 'name',
                    }])

    def test_predict(self):
        # Predict
        #
        self.run_test( "",
                None)
        self.run_test( "prediCt blah",
                [{
                    "instruction" : "predict",
                    "expression" : "blah",
                    }])
    def test_labeled_predict(self):
        self.run_test( "name : predict blah",
                [{
                    "instruction" : "labeled_predict",
                    "expression" : "blah",
                    "label" : 'name',
                    }])

    def test_observe(self):
        # Observe
        #
        self.run_test( "",
                None)
        self.run_test( "obServe blah = 1.3",
                [{
                    "instruction" : "observe",
                    "expression" : "blah",
                    "value" : {"type":"number", "value":1.3},
                    }])
    def test_labeled_observe(self):
        self.run_test( "name : observe a = count<32>",
                [{
                    "instruction" : "labeled_observe",
                    "expression" : "a",
                    "value" : {'type':'count', 'value':32.0},
                    "label" : 'name',
                    }])

    def test_forget(self):
        # Forget
        #
        self.run_test( "",
                None)
        self.run_test( "FORGET 34",
                [{
                    "instruction" : "forget",
                    "directive_id" : 34,
                    }])

    def test_labeled_forget(self):
        self.run_test( "forget blah",
                [{
                    "instruction" : "labeled_forget",
                    "label" : "blah",
                    }])

    def test_sample(self):
        # Sample
        #
        self.run_test( "",
                None)
        self.run_test( "saMple blah",
                [{
                    "instruction" : "sample",
                    "expression" : "blah",
                    }])

    def test_force(self):
        # Force
        #
        self.run_test( "",
                None)
        self.run_test( "force blah = count<132>",
                [{
                    "instruction" : "force",
                    "expression" : "blah",
                    "value" : {'type':'count', 'value':132.0},
                    }])

    def test_infer(self):
        # Infer
        #
        self.run_test( "",
                None)
        self.run_test( "infer 132",
                [{
                    "instruction" : "infer",
                    "iterations" : 132,
                    "resample" : False,
                    }])

    def test_program(self):
        self.expression = self.program
        self.run_test( "force blah = count<132> infer 132",
                [{
                    "instruction" : "force",
                    "expression" : "blah",
                    "value" : {'type':'count', 'value':132.0},
                    },{
                    "instruction" : "infer",
                    "iterations" : 132,
                    "resample" : False,
                    }])


class TestParserUtilsStack(ParserTestCase):
    def test_push_stack(self):
        stack = []
        s = utils.literal_token(stack)
        s.parseString(" int<1>")
        expected = [{
                "index" : 1,
                "children" : [],
                }]
        self.assertEquals(stack, expected)

    def test_nest_stack(self):
        stack = []
        symbol = utils.symbol_token(stack)
        value = utils.literal_token(stack)
        expression = utils.symbol_token(stack)
        instruction, program = utils.init_instructions(value, symbol, expression, stack)
        instruction.parseString("    assume a = web")
        expected = [{
                "index" : 4,
                "children" : [
                    {
                        "index": 11,
                        "children": [],
                    },{
                        "index": 15,
                        "children": [],
                        }
                    ],
                }]
        self.assertEquals(stack, expected)

    def test_get_text_index(self):
        stack = [{
                "index" : 4,
                "children" : [
                    {
                        "index": 11,
                        "children": [],
                    },{
                        "index": 15,
                        "children": [],
                        }
                    ],
                }]
        output1 = utils.get_text_index(stack,0)
        expected1 = 4
        self.assertEqual(output1, expected1)
        output2 = utils.get_text_index(stack,0, 1)
        expected2 = 15
        self.assertEqual(output2, expected2)

    def test_get_parse_tree_index(self):
        stack = [{
                "index" : 4,
                "children" : [
                    {
                        "index": 11,
                        "children": [],
                    },{
                        "index": 15,
                        "children": [],
                        }
                    ],
                }]
        output1 = utils.get_parse_tree_index(stack,16)
        expected1 = [0,1]
        self.assertEquals(output1, expected1)
        output2 = utils.get_parse_tree_index(stack,15)
        expected2 = [0,1]
        self.assertEquals(output2, expected2)
        try:
            utils.get_parse_tree_index(stack,3)
        except VentureException as e:
            self.assertEqual(e.exception, 'fatal')

    def test_apply_parser(self):
        element = utils.symbol_token()
        try:
            utils.apply_parser(element,' 12398awefj')
        except VentureException as e:
            self.assertEqual(e.exception, 'text_parse')
            self.assertEqual(e.data['index'], 1)
        try:
            utils.apply_parser(element,2)
        except VentureException as e:
            self.assertEqual(e.exception, 'fatal')
        output = utils.apply_parser(element,'awef')
        self.assertEqual(output,['awef'])

if __name__ == '__main__':
    unittest.main()
