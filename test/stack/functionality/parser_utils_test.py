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
# -*- coding: utf-8 -*-
from nose.plugins.attrib import attr

from venture.exception import VentureException
from venture.parser import utils
from venture.test.test_helpers import ParserTestCase
import venture.value.dicts as v

def r(a,b,c):
    return [{"loc":[a,a+b-1], "value":c}]

def j(*args):
    mins = []
    maxes = []
    for a, b in zip(*(iter(args),)*2):
        mins.append(a)
        maxes.append(a+b-1)
    return [min(mins), max(maxes)]

# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestParserUtilsAtoms(ParserTestCase):
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
                r(0,1,'add'))
        self.run_test( "lambda",
                None)
        self.run_test( "if",
                None)
        self.run_test( "awef123",
                r(0,7,"awef123"))
        self.run_test( r'awe!@#e',
                None)

    def test_number(self):
        # Number
        #
        self.expression = utils.number_token()
        self.run_test( "",
                None)
        self.run_test( "3",
                r(0,1,3.0))
        self.run_test( "-3.22",
                r(0,5,-3.22))
        self.run_test( "3.",
                r(0,2,3.0))
        self.run_test( "-.3",
                r(0,3,-.3))
        self.run_test( "-.3e-2",
                r(0,6,-.3e-2))
        self.run_test( "moo",
                None)

    def test_integer(self):
        # Integer
        #
        self.expression = utils.integer_token()
        self.run_test( "",
                None)
        self.run_test( "3",
                r(0,1,3))
        self.run_test( "moo",
                None)


    def test_string(self):
        # String
        #
        self.expression = utils.string_token()
        self.run_test( r'',
                None)
        self.run_test( r'"abc"',
                r(0,5,r'abc'))
        self.run_test( r'"\""',
                r(0,4,r'"'))
        self.run_test( r'"\n"',
                r(0,4,'\n'))
        self.run_test( r'"\t"',
                r(0,4,'\t'))
        self.run_test( r'"\f"',
                r(0,4,'\f'))
        self.run_test( r'"\062"',
                r(0,6,'2'))
        self.run_test( r'"\462"',
                None)

    def test_null(self):
        # Null
        #
        self.expression = utils.null_token()
        self.run_test( "",
                None)
        self.run_test( "null",
                r(0,4,None))

    def test_boolean(self):
        # Boolean
        #
        self.expression = utils.boolean_token()
        self.run_test( "",
                None)
        self.run_test( "true",
                r(0,4,True))
        self.run_test( "false",
                r(0,5,False))

    def test_json_value(self):
        # Json value
        #
        self.expression = utils.json_value_token()
        self.run_test( "",
                None)
        self.run_test( r'"abc"',
                r(0,5,r'abc'))
        self.run_test( r'2.3',
                r(0,3,2.3))
        self.run_test( "null",
                r(0,4,None))
        self.run_test( "true",
                r(0,4,True))
        self.run_test( "[1,2,[3,[]]]",
                r(0,12,[1,2,[3,[]]]))
        self.run_test( '{"a":{"b":{}},"c":"d"}',
                r(0,22,{"a":{"b":{}}, "c":"d"}))

    def test_value(self):
        # Value
        #
        self.expression = utils.value_token()
        self.run_test( "", None)
        self.run_test( "boolean<true>", None)
        self.run_test( "number<1.0>", None)
        self.run_test( "real<1.0>", r(0,9,v.real(1.0)))
        self.run_test( 'url<"www.google.com">',
                       r(0,21,v.val("url", "www.google.com")))
        self.run_test( 'simplex_point<[0.5,0.5]>',
                       r(0,24,v.val("simplex_point", [0.5,0.5])))
        self.run_test( 'costume<{"hat_color":"blue","shirt_color":"red"}>',
                       r(0,49,v.val("costume", {"hat_color":"blue", "shirt_color":"red"})))


    def test_number_literal(self):
        # Number Literal
        #
        self.expression = utils.number_literal_token()
        self.run_test( "", None)
        self.run_test( "1", r(0,1,v.number(1.0)))


    def test_boolean_literal(self):
        # Boolean Literal
        #
        self.expression = utils.boolean_literal_token()
        self.run_test( "", None)
        self.run_test( "true", r(0,4,v.boolean(True)))


    def test_literal_token(self):
        # Literal
        #
        self.expression = utils.literal_token()
        self.run_test( "", None)
        self.run_test( "1", r(0,1,v.number(1.0)))
        self.run_test( "true", r(0,4,v.boolean(True)))
        self.run_test( "real<1.0>", r(0,9,v.real(1.0)))






# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestParserUtilsStuff(ParserTestCase):
    A = {"loc":j(12,5,43,4,90,3,100,5,123,1), "value":{
            "instruction":{"loc":j(12,5), "value":"asume"},
            "expression": {"loc":j(43,4,90,3,100,5), "value":[
                {"loc": j(44,3), "value":"moo"},
                {"loc":j(90,3,100,4), "value":[
                    {'loc':j(90,3), "value":"poo"},
                    {'loc':j(100,3), "value":"foo"},
                    ]},
                ]},
            "symbol" : {"loc":j(123,1), "value": "q"},
            }}
    B = {
            "instruction":"asume",
            "expression":['moo',['poo','foo']],
            "symbol":"q",
            }
    C = {
            "instruction":j(12,5),
            "expression":j(43,4,90,3,100,5),
            "symbol":j(123,1),
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
        b = [j(12,5,43,4,90,3,100,5,123,1)]*3
        output = utils.split_program_parse_tree(a)
        self.assertEqual(output, b)

    def test_get_text_index(self):
        a = self.A['value']['expression']
        output = utils.get_text_index(a,[])
        self.assertEqual(output, j(43,4,90,3,100,5))
        output = utils.get_text_index(a, [0])
        self.assertEqual(output, j(44,3))
        output = utils.get_text_index(a, [1])
        self.assertEqual(output, j(90,3,100,4))
        output = utils.get_text_index(a, [1,0])
        self.assertEqual(output, j(90,3))
        output = utils.get_text_index(a, [1,1])
        self.assertEqual(output, j(100,3))

    def test_expression_index(self):
        a = self.A['value']['expression']
        try:
            output = utils.get_expression_index(a, 42)
        except VentureException as e:
            self.assertEqual(e.exception, 'no_expression_index')
        output = utils.get_expression_index(a, 43)
        self.assertEqual(output, [])
        output = utils.get_expression_index(a, 50)
        self.assertEqual(output, [])
        output = utils.get_expression_index(a, 44)
        self.assertEqual(output, [0])
        output = utils.get_expression_index(a, 45)
        self.assertEqual(output, [0])
        output = utils.get_expression_index(a, 90)
        self.assertEqual(output, [1,0])

    def test_program_string_fragments(self):
        s = '0123456789'
        f = [j(1,2), j(3,4), j(9,1)]
        output = utils.get_program_string_fragments(s, f)
        self.assertEqual(output, ['12','3456','9'])

    def test_instruction_string_fragments(self):
        s = 'name : assume x = 14 + 15'
        f = {
                "label":j(0,4),
                "instruction":j(7,6),
                "symbol":j(14,1),
                "expression":j(18,7),
                }
        e = {
                "label":"name",
                "instruction":"assume",
                "symbol":"x",
                "expression":"14 + 15",
                }
        output = utils.get_instruction_string_fragments(s, f)
        self.assertEqual(output, e)

    def test_apply_parser(self):
        element = utils.symbol_token()
        try:
            utils.apply_parser(element,' 12398awefj')
        except VentureException as e:
            self.assertEqual(e.exception, 'text_parse')
            self.assertEqual(e.data['text_index'], j(1,1))
        try:
            utils.apply_parser(element,2)
        except VentureException as e:
            self.assertEqual(e.exception, 'fatal')
        output = utils.apply_parser(element,'awef')
        self.assertEqual(output,[{"loc":j(0,4), "value":'awef'}])

    def test_value_to_string(self):
        output = utils.value_to_string("real<1>")
        self.assertEqual(output, "real<1>")
        output = utils.value_to_string(v.real(1))
        self.assertEqual(output, "real<1>")
        output = utils.value_to_string(v.number(1))
        self.assertEqual(output, "1")
        output = utils.value_to_string(v.boolean(True))
        self.assertEqual(output, 'true')
        try:
            utils.value_to_string(v.real(1))
        except VentureException as e:
            self.assertEqual(e.exception, "fatal")
        output = utils.value_to_string(1)
        self.assertEqual(output, "1")
        output = utils.value_to_string(True)
        self.assertEqual(output, "true")

    def test_substitute_params_list(self):
        output = utils.substitute_params('abc',[])
        self.assertEquals(output, 'abc')
        output = utils.substitute_params('abc%%',[])
        self.assertEquals(output, 'abc%')
        output = utils.substitute_params('abc%s',['d'])
        self.assertEquals(output, 'abcd')
        output = utils.substitute_params('abc%v',[True])
        self.assertEquals(output, 'abctrue')
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%s',[])
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%',[])
        with self.assertRaises(VentureException):
            utils.substitute_params('abc',['d'])

    def test_substitute_params_dict(self):
        output = utils.substitute_params('abc',{})
        self.assertEquals(output, 'abc')
        output = utils.substitute_params('abc%%',{})
        self.assertEquals(output, 'abc%')
        output = utils.substitute_params('abc%(x)s',{'x':'d'})
        self.assertEquals(output, 'abcd')
        output = utils.substitute_params('abc%(%)j',{'%':{}})
        self.assertEquals(output, 'abc{}')
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%()s',{})
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%(s)',{})
        with self.assertRaises(VentureException):
            utils.substitute_params('abc%s',{})


