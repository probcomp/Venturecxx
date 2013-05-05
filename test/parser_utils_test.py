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


    def test_location_wrapper(self):
        # Literal
        #
        self.expression = utils.location_wrapper(utils.literal_token())
        self.run_test( " 1",
                [{"loc":1, "value":{"type":"number", "value":1.0}}])









class TestParserUtilsInstructions(ParserTestCase):
    def setUp(self):
        symbol = utils.location_wrapper(utils.symbol_token())
        value = utils.location_wrapper(utils.literal_token())
        expression = utils.location_wrapper(utils.symbol_token())   #for simplicity
        self.instruction, self.program = utils.init_instructions(value, symbol, expression)
        self.expression = self.instruction


    def test_assume(self):
        # Assume
        #
        self.run_test( "assuMe blah = moo",
                [{"loc": 0, "value":{
                    "instruction" : {"loc": 0, "value":"assume"},
                    "symbol" : {"loc": 7, "value":"blah"},
                    "expression" : {"loc":14, "value":"moo"},
                    }}])
    
    def test_labeled_assume(self):
        self.run_test( "name : assume a = b",
                [{"loc":0, "value":{
                    "instruction" : {"loc":7, "value":"labeled_assume"},
                    "symbol" : {"loc": 14, "value":"a"},
                    "expression" : {"loc":18, "value":"b"},
                    "label" : {"loc":0, "value":'name'},
                    }}])

    def test_predict(self):
        # Predict
        #
        self.run_test( "  prediCt blah",
                [{"loc":2, "value":{
                    "instruction" : {"loc":2, "value":"predict"},
                    "expression" : {"loc":10, "value":"blah"},
                    }}])
    def test_labeled_predict(self):
        self.run_test( "name : predict blah",
                [{"loc":0, "value":{
                    "instruction" : {"loc":7, "value":"labeled_predict"},
                    "expression" : {"loc":15, "value":"blah"},
                    "label" : {"loc":0, "value":'name'},
                    }}])

    def test_observe(self):
        # Observe
        #
        self.run_test( "obServe blah = 1.3",
                [{"loc":0, "value":{
                    "instruction" : {"loc":0, "value":"observe"},
                    "expression" : {"loc":8, "value":"blah"},
                    "value" : {"loc": 15, "value":{"type":"number", "value":1.3}},
                    }}])
    def test_labeled_observe(self):
        self.run_test( "name : observe a = count<32>",
                [{"loc":0, "value":{
                    "instruction" : {"loc":7, "value":"labeled_observe"},
                    "expression" : {"loc":15, "value":"a"},
                    "value" : {"loc":19, "value":{'type':'count', 'value':32.0}},
                    "label" : {"loc":0, "value":'name'},
                    }}])

    def test_forget(self):
        # Forget
        #
        self.run_test( "FORGET 34",
                [{"loc":0, "value":{
                    "instruction" : {"loc":0, "value":"forget"},
                    "directive_id" : {"loc":7, "value":34},
                    }}])

    def test_labeled_forget(self):
        self.run_test( "forget blah",
                [{"loc":0, "value":{
                    "instruction" : {"loc":0, "value":"labeled_forget"},
                    "label" : {"loc":7, "value":"blah"},
                    }}])

    def test_sample(self):
        # Sample
        #
        self.run_test( "saMple blah",
                [{"loc":0, "value":{
                    "instruction" : {"loc":0, "value":"sample"},
                    "expression" : {"loc":7, "value":"blah"},
                    }}])

    def test_force(self):
        # Force
        #
        self.run_test( "force blah = count<132>",
                [{"loc":0, "value":{
                    "instruction" : {"loc":0, "value":"force"},
                    "expression" : {"loc":6, "value":"blah"},
                    "value" : {"loc":13, "value":{'type':'count', 'value':132.0}},
                    }}])

    def test_infer(self):
        # Infer
        #
        self.run_test( " infer 132",
                [{"loc":1, "value":{
                    "instruction" : {"loc":1, "value":"infer"},
                    "iterations" : {"loc":7, "value":132},
                    "resample" : {"loc":1, "value":False},
                    }}])

    def test_program(self):
        self.expression = self.program
        self.run_test( "force blah = count<132> infer 132",
                [{"loc":0, "value":[
                    {"loc":0, "value":{
                        "instruction" : {"loc":0, "value":"force"},
                        "expression" : {"loc":6, "value":"blah"},
                        "value" : {"loc":13, "value":{'type':'count', 'value':132.0}},
                        }},{"loc":24, "value":{
                        "instruction" : {"loc":24, "value":"infer"},
                        "iterations" : {"loc":30 , "value":132},
                        "resample" : {"loc":24, "value":False},
                    }}]}])


                



class TestParserUtilsStuff(ParserTestCase):
    A = {"loc":14, "value":{
            "instruction":{"loc":12, "value":"asume"},
            "expression": {"loc":43, "value":[
                {"loc": 44, "value":"moo"},
                {"loc":90, "value":[
                    {'loc':90, "value":"poo"},
                    {'loc':100, "value":"foo"},
                    ]},
                ]},
            "symbol" : {"loc":123, "value": "q"},
            }}
    B = {
            "instruction":"asume",
            "expression":['moo',['poo','foo']],
            "symbol":"q",
            }
    C = {
            "instruction":12,
            "expression":43,
            "symbol":123,
            }
    
    def test_simplify_expression_parse_tree(self):
        a = self.A['value']['expression']
        b = self.B['expression']
        output = utils.simplify_expression_parse_tree(a)
        self.assertEqual(output, b)

    def test_simplify_instruction_parse_tree(self):
        a = self.A
        b = self.B
        output = utils.simplify_instruction_parse_tree(a)
        self.assertEqual(output, b)

    def test_simplify_program_parse_tree(self):
        a = {"loc":0, "value":[self.A]*3}
        b = [self.B]*3
        output = utils.simplify_program_parse_tree(a)
        self.assertEqual(output, b)
    
    def test_split_instruction_parse_tree(self):
        a = self.A
        b = self.C
        output = utils.split_instruction_parse_tree(a)
        self.assertEqual(output, b)

    def test_split_program_parse_tree(self):
        a = {"loc":0, "value":[self.A]*3}
        b = [14]*3
        output = utils.split_program_parse_tree(a)
        self.assertEqual(output, b)

    def test_get_text_index(self):
        a = self.A['value']['expression']
        output = utils.get_text_index(a,[])
        self.assertEqual(output, 43)
        output = utils.get_text_index(a, [0])
        self.assertEqual(output, 44)
        output = utils.get_text_index(a, [1])
        self.assertEqual(output, 90)
        output = utils.get_text_index(a, [1,0])
        self.assertEqual(output, 90)
        output = utils.get_text_index(a, [1,1])
        self.assertEqual(output, 100)

    def test_expression_index(self):
        a = self.A['value']['expression']
        try:
            output = utils.get_expression_index(a, 42)
        except VentureException as e:
            self.assertEqual(e.exception = 'no_expression_index')
        output = utils.get_expression_index(a, 43)
        self.assertEqual(output, [])
        output = utils.get_expression_index(a, 44)
        self.assertEqual(output, [0])
        output = utils.get_expression_index(a, 45)
        self.assertEqual(output, [0])
        output = utils.get_expression_index(a, 90)
        self.assertEqual(output, [1,0])

    def test_get_string_fragments(self):
        s = '0123456789'
        f = [1, 5, 9]
        output = utils.get_string_fragments(s, f)
        self.assertEqual(output, ['1234','5678','9'])


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
