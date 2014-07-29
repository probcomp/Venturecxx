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

from venture.parser import VentureScriptParser
import venture.parser.venture_script_parser as module
from venture.test.test_helpers import ParserTestCase
import venture.value.dicts as v

exponent_ops = [('**','pow')]
add_sub_ops = [('+', 'add'), ('-','sub')]
mul_div_ops = [('*','mul'), ('/','div')]
comparison_ops = [('<=', 'lte'), ('>=', 'gte'), ('<', 'lt'),('>', 'gt')]
equality_ops = [('==','eq'),('!=', 'neq')]
boolean_and_ops = [('&&', 'and')]
boolean_or_ops = [('||','or')]

def r(*args):
    return [{"loc":[a,a+b-1], "value":c} for a,b,c in zip(*(iter(args),)*3)]

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
class TestVentureScriptParserAtoms(ParserTestCase):
    _multiprocess_can_split_ = True

    def setUp(self):
        self.p = VentureScriptParser.instance()

    def test_collapse_identity(self):
        # "((a+b))"
        a = {"loc":[0,6],"value":[
                {"loc":[0,6], "value":'identity'},
                {"loc":[1,5], "value":[
                    {"loc":[1,5], "value":'identity'},
                    {"loc":[2,4], "value":[
                        {"loc":[2,2], "value":'+'},
                        {"loc":[3,3], "value":'a'},
                        {"loc":[4,4], "value":'b'},
                        ]}
                    ]}
                ]}
        b = {"loc":[0,6],"value":[
                {"loc":[0,6], "value":'identity'},
                {"loc":[1,5], "value":[
                    {"loc":[2,2], "value":'+'},
                    {"loc":[3,3], "value":'a'},
                    {"loc":[4,4], "value":'b'},
                    ]}
                ]}
        output = module._collapse_identity(a,('+'))
        self.assertEqual(output,b)
        # " a+b"
        a = {"loc":[1,3], "value":[
                {"loc":[1,1], "value":'+'},
                {"loc":[2,2], "value":'a'},
                {"loc":[3,3], "value":'b'},
                ]}
        output = module._collapse_identity(a,('+'))
        self.assertEqual(output,a)
        # " (a)"
        a = {"loc":[1,3], "value":[
                {"loc":[1,3], "value":'identity'},
                {"loc":[2,2], "value":'a'},
                ]}
        output = module._collapse_identity(a,('+'))
        self.assertEqual(output,a)
        # " a"
        a = {"loc":[1,1], "value":'a'}
        output = module._collapse_identity(a,('+'))
        self.assertEqual(output,a)

    def test_symbol_args(self):
        self.expression = self.p.symbol_args
        self.run_test( "()",
                r(0,2,[]))
        self.run_test( "(a)",
                r(0,3,r(1,1,'a')))
        self.run_test( "(a, b)",
                r(0,6,r(1,1,"a",4,1,'b')))


    def test_expression_args(self):
        self.expression = self.p.expression_args
        self.run_test( "()",
                r(0,2,r()))
        self.run_test( "(a)",
                r(0,3,r(1,1,'a')))
        self.run_test( "(a, b)",
                r(0,6,r(1,1,'a',4,1,'b')))


    def test_assignments(self):
        self.expression = self.p.assignments
        self.run_test( "a=b",
                r(0,3,r(0,3,r(0,1,'a',2,1,'b'))))
        self.run_test( "a=b c=d",
                r(0,7,r(0,3,r(0,1,'a',2,1,'b'),4,3,r(4,1,'c',6,1,'d'))))

    def test_optional_let(self):
        self.expression = self.p.optional_let
        self.run_test( "a",
                r(0,1,"a"))
        self.run_test( "a=b c",
                r(0,5,r(0,5,'let',0,3,r(0,3,r(0,1,'a',2,1,'b')),4,1,"c")))
        self.run_test( "{a=b c}",
                None)



    def test_proc(self):
        self.expression = self.p.proc
        self.run_test( "proc(arg, arg){ true }",
                r(0,22,r(0,4,"lambda",4,10,r(5,3,"arg",10,3,"arg"),16,4,v.boolean(True))))
        self.run_test( "proc(){ a=b c }",
                r(0,15,r(0,4,"lambda",4,2,r(),8,5,r(8,5,'let',8,3,r(8,3,r(8,1,"a",10,1,'b')),12,1,"c"))))


    def test_let(self):
        self.expression = self.p.let
        self.run_test( "{ a=b c=d e}",
                r(0,12,r(0,12,"let",2,7,r(2,3,r(2,1,'a',4,1,'b'),6,3,r(6,1,'c',8,1,'d')),10,1,"e")))


    def test_identity(self):
        self.expression = self.p.identity
        self.run_test( "(a)",
                r(0,3,r(0,3,"identity",1,1,'a')))


    def test_if_else(self):
        self.expression = self.p.if_else
        self.run_test( "if (a) { b }else {c}",
                r(0,20,r(0,2,"if",4,1,"a",9,1,"b",18,1,"c")))
        self.run_test( "if( a=b c) {d=e f}else{g=h i }",
                r(0,30,r(0,2,"if",
                    4,5,r(4,5,'let',4,3,r(4,3,r(4,1,"a",6,1,"b")),8,1,"c"),
                    12,5,r(12,5,'let',12,3,r(12,3,r(12,1,"d",14,1,"e")),16,1,"f"),
                    23,5,r(23,5,'let',23,3,r(23,3,r(23,1,"g",25,1,"h")),27,1,"i"),
                )))

    def test_infix_locations(self):
        self.expression = self.p.expression
        self.run_test( "a+(b+c)",
                r(0,7,r(1,1,'add',0,1,'a',2,5,r(4,1,'add',3,1,'b',5,1,'c')))
                )


    # I'm not going to bother augmenting all of the
    # previous tests to include line numbers etc.
    # Instead, use a different test handler

    def test_function_application(self):
        self.run_legacy_test( "a(b)(c)",
                [[['a', 'b'], 'c']],
                "fn_application")
        self.run_legacy_test( "a(b, c)",
                [['a', 'b', 'c']],
                "fn_application")
        self.run_legacy_test( "a()",
                [['a']],
                "fn_application")
        # Function application has precedence over all infix operators
        for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( "a" + x + "b()",
                    [[y, 'a', ['b']]],
                    "expression")
        # Collapse identities with lesser precedence
        for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( "(a" + x + "b)()",
                    [[[y, "a", "b"]]],
                    "fn_application")
        # Collapse nested identities
        self.run_legacy_test( "((a+b))()",
                [[['identity',['add', 'a', 'b']]]],
                "fn_application")


    def test_the_rest_of_the_shizzle(self):
        self.run_legacy_test( "a**b**c",
                [['pow', 'a', ['pow', 'b', 'c']]],
                "exponent")
        # Don't collapse redundant identities
        self.run_legacy_test( "a**(b**c)",
                [['pow', 'a', ['identity', ['pow', 'b', 'c']]]],
                "exponent")
        # Collapse non-redundant identities
        self.run_legacy_test( "(a**b)**c",
                [['pow', ['pow', 'a', 'b'], 'c']],
                "exponent")
        self.run_legacy_test( "((a**b))**c",
                [['pow', ['identity', ['pow', 'a', 'b']], 'c']],
                "exponent")
        # Collapse identities with lesser precedence
        for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + equality_ops + add_sub_ops + mul_div_ops:
            self.run_legacy_test( "(a" + x + "b)**c",
                    [['pow',[y, "a", "b"], "c"]],
                    "exponent")



        # Multiplication and division
        #
        self.run_legacy_test( "",
                None,
                "mul_div")
        self.run_legacy_test( "a*b/c",
                [['div',['mul', 'a', 'b'], 'c']],
                "mul_div")
        self.run_legacy_test( "a/b*c",
                [['mul',['div', 'a', 'b'], 'c']],
                "mul_div")
        # Don't collapse redundant identities
        self.run_legacy_test( "(a*b)/c",
                [['div',['identity', ['mul', 'a', 'b']], 'c']],
                "mul_div")
        self.run_legacy_test( "(a/b)*c",
                [['mul',['identity', ['div', 'a', 'b']], 'c']],
                "mul_div")
        # Collapse identities with equal precedence
        self.run_legacy_test( "a*(b/c)",
                [['mul', 'a', ['div', 'b', 'c']]],
                "mul_div")
        self.run_legacy_test( "a/(b*c)",
                [['div', 'a', ['mul', 'b', 'c']]],
                "mul_div")
        # Collapse nested identies
        self.run_legacy_test( "a/((b/c))",
                [['div', 'a', ['identity', ['div', 'b', 'c']]]],
                "mul_div")
        self.run_legacy_test( "a*(((b*c)))",
                [['mul', 'a', ['identity', ['identity', ['mul', 'b', 'c']]]]],
                "mul_div")
        # Test that mul_div has medium precedence
        for x, y in exponent_ops:
            self.run_legacy_test( "a" + x + "b*c",
                    [['mul', [y, "a", "b"], 'c']],
                    "mul_div")
        # Collapse identities with lesser precedence
        for x, y in boolean_and_ops + boolean_or_ops + equality_ops + comparison_ops + add_sub_ops:
            self.run_legacy_test( "(a" + x + "b)*c",
                    [['mul',[y, "a", "b"], 'c']],
                    "mul_div")
        # Don't collapse identities with greater precedence
        for x, y in exponent_ops:
            self.run_legacy_test( "(a" + x + "b)*c",
                    [['mul',['identity',[y, "a", "b"]], 'c']],
                    "mul_div")



        # Addition and subtraction
        #
        self.run_legacy_test( "",
                None,
                "add_sub")
        self.run_legacy_test( "a+b-c",
                [['sub',['add', 'a', 'b'], 'c']],
                "add_sub")
        self.run_legacy_test( "a-b+c",
                [['add',['sub', 'a', 'b'], 'c']],
                "add_sub")
        # Don't collapse redundant identities
        self.run_legacy_test( "(a+b)-c",
                [['sub',['identity', ['add', 'a', 'b']], 'c']],
                "add_sub")
        self.run_legacy_test( "(a-b)+c",
                [['add',['identity', ['sub', 'a', 'b']], 'c']],
                "add_sub")
        # Collapse identities with equal precedence
        self.run_legacy_test( "a+(b-c)",
                [['add', 'a', ['sub', 'b', 'c']]],
                "add_sub")
        self.run_legacy_test( "a-(b+c)",
                [['sub', 'a', ['add', 'b', 'c']]],
                "add_sub")
        # Collapse nested identies
        self.run_legacy_test( "a-((b-c))",
                [['sub', 'a', ['identity', ['sub', 'b', 'c']]]],
                "add_sub")
        self.run_legacy_test( "a+(((b+c)))",
                [['add', 'a', ['identity', ['identity', ['add', 'b', 'c']]]]],
                "add_sub")
        # Test that add_sub has medium precedence
        for x, y in exponent_ops + mul_div_ops:
            self.run_legacy_test( "a" + x + "b+c",
                    [['add', [y, "a", "b"], 'c']],
                    "add_sub")
        # Collapse identities with lesser precedence
        for x, y in boolean_and_ops + boolean_or_ops + equality_ops + comparison_ops:
            self.run_legacy_test( "(a" + x + "b)+c",
                    [['add',[y, "a", "b"], 'c']],
                    "add_sub")
        # Don't collapse identities with greater precedence
        for x, y in exponent_ops + mul_div_ops:
            self.run_legacy_test( "(a" + x + "b)+c",
                    [['add',['identity',[y, "a", "b"]], 'c']],
                    "add_sub")

        # Comparison
        #
        self.run_legacy_test( "",
                None,
                "comparison")
        self.run_legacy_test( "a<b<c",
                [['lt',['lt', 'a', 'b'],'c']],
                "comparison")
        # Test all operators
        for x, y in comparison_ops:
            self.run_legacy_test( "a" + x + "b",
                    [[y, "a", "b"]],
                    "comparison")
        # Test that comparison has low precedence
        for x, y in add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( "a" + x + "b<c",
                    [['lt', [y, "a", "b"], 'c']],
                    "comparison")
        # Collapse identities with lesser precedence
        for x, y in boolean_and_ops + boolean_or_ops + equality_ops:
            self.run_legacy_test( "(a" + x + "b)<c",
                    [['lt',[y, "a", "b"], 'c']],
                    "comparison")
        # Don't collapse identities with greater precedence
        for x, y in mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( "(a" + x + "b)<c",
                    [['lt',['identity',[y, "a", "b"]], 'c']],
                    "comparison")
        # Collapse identities of equal precedence
        self.run_legacy_test( "(a>b)<(c>d)",
                [['lt',['identity',['gt', 'a', 'b']], ['gt', 'c', 'd']]],
                "comparison")
        # Collapse nested identities
        self.run_legacy_test( "a<((b>c))",
                [['lt', 'a', ['identity', ['gt', 'b', 'c']]]],
                "comparison")

        # Equality
        #
        self.run_legacy_test( "",
                None,
                "equality")
        self.run_legacy_test( "a==b==c",
                [['eq',['eq', 'a', 'b'],'c']],
                "equality")
        # Test all operators
        for x, y in equality_ops:
            self.run_legacy_test( "a" + x + "b",
                    [[y, "a", "b"]],
                    "equality")
        # Test that equality has low precedence
        for x, y in add_sub_ops + mul_div_ops + exponent_ops + comparison_ops:
            self.run_legacy_test( "a" + x + "b==c",
                    [['eq', [y, "a", "b"], 'c']],
                    "equality")
        # Collapse identities with lesser precedence
        for x, y in boolean_and_ops + boolean_or_ops:
            self.run_legacy_test( "(a" + x + "b)==c",
                    [['eq',[y, "a", "b"], 'c']],
                    "equality")
        # Don't collapse identities with greater precedence
        for x, y in mul_div_ops + exponent_ops + add_sub_ops + comparison_ops:
            self.run_legacy_test( "(a" + x + "b)==c",
                    [['eq',['identity',[y, "a", "b"]], 'c']],
                    "equality")
        # Collapse identities of equal precedence
        self.run_legacy_test( "(a!=b)==(c!=d)",
                [['eq',['identity',['neq', 'a', 'b']], ['neq', 'c', 'd']]],
                "equality")
        # Collapse nested identities
        self.run_legacy_test( "a==((b!=c))",
                [['eq', 'a', ['identity', ['neq', 'b', 'c']]]],
                "equality")


        # And
        #
        self.run_legacy_test( "",
                None,
                "boolean_and")
        self.run_legacy_test( "a && b && c",
                [['and', ['and', 'a', 'b'], 'c']],
                "boolean_and")
        # Don't collapse redundant identities
        self.run_legacy_test( "(a&&b)&&c",
                [['and', ['identity', ['and', 'a', 'b']], 'c']],
                "boolean_and")
        # Collapse non-redundant identities
        self.run_legacy_test( "a&&(b&&c)",
                [['and', 'a', ['and', 'b', 'c']]],
                "boolean_and")
        # Collapse nested identities
        self.run_legacy_test( "a&&((b&&c))",
                [['and', 'a', ['identity', ['and', 'b', 'c']]]],
                "boolean_and")
        # Test that and has low precedence
        for x, y in comparison_ops + equality_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( "a" + x + "b&&c",
                    [['and', [y, "a", "b"], 'c']],
                    "boolean_and")
        # Collapse identities with lesser precedence
        for x, y in boolean_or_ops:
            self.run_legacy_test( "(a" + x + "b)&&c",
                    [['and',[y, "a", "b"], 'c']],
                    "boolean_and")
        # Don't collapse identities with greater precedence
        for x, y in comparison_ops + equality_ops + mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( "(a" + x + "b)&&c",
                    [['and',['identity',[y, "a", "b"]], 'c']],
                    "boolean_and")

        # Or
        #
        self.run_legacy_test( "",
                None,
                "boolean_or")
        self.run_legacy_test( "a || b || c",
                [['or', ['or', 'a', 'b'], 'c']],
                "boolean_or")
        # Don't collapse redundant identities
        self.run_legacy_test( "(a||b)||c",
                [['or', ['identity', ['or', 'a', 'b']], 'c']],
                "boolean_or")
        # Collapse non-redundant identities
        self.run_legacy_test( "a||(b||c)",
                [['or', 'a', ['or', 'b', 'c']]],
                "boolean_or")
        # Collapse nested identities
        self.run_legacy_test( "a||((b||c))",
                [['or', 'a', ['identity', ['or', 'b', 'c']]]],
                "boolean_or")
        # Test that or has low precedence
        for x, y in comparison_ops + equality_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( "a" + x + "b||c",
                    [['or', [y, "a", "b"], 'c']],
                    "boolean_or")
        # Don't collapse identities with greater precedence
        for x, y in comparison_ops + equality_ops + mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( "(a" + x + "b)||c",
                    [['or',['identity',[y, "a", "b"]], 'c']],
                    "boolean_or")


        # Expression
        #
        self.run_legacy_test( "",
                None,
                "expression")
        #identity
        self.run_legacy_test( "(a)",
                [["identity", 'a']],
                "expression")
        #let
        self.run_legacy_test( "{ a=b c=d e}",
                [["let", [['a','b'], ['c','d']], "e"]],
                "expression")
        #proc
        self.run_legacy_test( "proc(){ a=2 b }",
                [["lambda",[],['let',[["a", v.number(2.0)]], "b"]]],
                "expression")
        #symbol
        self.run_legacy_test( "b",
                ['b'],
                "expression")
        #literal
        self.run_legacy_test( "3",
                [v.number(3.0)],
                "expression")
        #if_else
        self.run_legacy_test( "if (a) { b }else {c}",
                [["if", "a", "b", "c"]],
                "expression")
        #function application
        self.run_legacy_test( "a(b)(c)",
                [[['a', 'b'], 'c']],
                "expression")
        #exponentiation
        self.run_legacy_test( "a**b**c",
                [['pow', 'a', ['pow', 'b', 'c']]],
                "expression")
        #mul_div
        self.run_legacy_test( "a*b/c",
                [['div',['mul', 'a', 'b'], 'c']],
                "expression")
        #add_sub
        self.run_legacy_test( "a+b-c",
                [['sub',['add', 'a', 'b'], 'c']],
                "expression")
        #comparision
        self.run_legacy_test( "a==b==c",
                [['eq', ['eq', 'a', 'b'], 'c']],
                "expression")
        #boolean
        self.run_legacy_test( "true && true || true",
                [['or', ['and', v.boolean(True), v.boolean(True)], v.boolean(True)]],
                "expression")


        #fancy expression
        self.run_legacy_test( """
        (1 + 4)/3**5.11 + 32*4-2
        """,
                [['sub',
                            ['add',
                                ['div',['add',v.number(1.0),v.number(4.0)],['pow',v.number(3.0),v.number(5.11)]],
                                ['mul',v.number(32.0),v.number(4.0)],
                                ],
                            v.number(2.0)]],
                "expression")


# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestVentureScriptParser(ParserTestCase):
    def setUp(self):
        self.p = VentureScriptParser.instance()

    def test_parse_instruction(self):
        output = self.p.parse_instruction('assume a = b(c,d)')
        expected = {'instruction':'assume', 'symbol':'a', 'expression':['b','c','d']}
        self.assertEqual(output,expected)

    def test_split_program(self):
        output = self.p.split_program(" force blah = count<132> infer 132")
        instructions = ['force blah = count<132>','infer 132']
        indices = [[1,23],[25,33]]
        self.assertEqual(output,[instructions, indices])

    def test_split_instruction(self):
        output = self.p.split_instruction(" force blah = count<132>")
        indices = {
                "instruction": [1,5],
                "expression": [7,10],
                "value": [14,23],
                }
        strings = {
                "instruction": "force",
                "expression": "blah",
                "value": "count<132>",
                }
        self.assertEqual(output,[strings,indices])

    def test_expression_index_to_text_index(self):
        # "(a b (c (d e) f ))"
        s = "a(b,c(d(e),f))"
        f = self.p.expression_index_to_text_index
        output = f(s, [0])
        self.assertEqual(output, [0,0])
        output = f(s, [2])
        self.assertEqual(output, [4,12])
        output = f(s, [2,0])
        self.assertEqual(output, [4,4])
        output = f(s, [2,1,1])
        self.assertEqual(output, [8,8])


    def test_character_index_to_expression_index(self):
        # "(a b (c (d e) f ))"
        s = "a( b,c(d(e),f))"
        f = self.p.character_index_to_expression_index
        output = f(s, 1)
        self.assertEqual(output, [])
        output = f(s, 0)
        self.assertEqual(output, [0])
        output = f(s, 2)
        self.assertEqual(output, [])
        output = f(s, 6)
        self.assertEqual(output, [2])
        output = f(s, 5)
        self.assertEqual(output, [2,0])

    def test_get_instruction_string(self):
        f = self.p.get_instruction_string
        output = f('observe')
        self.assertEqual(output,'observe %(expression)s = %(value)v')
        output = f('infer')
        self.assertEqual(output,'infer %(expression)s')


# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestInstructions(ParserTestCase):
    def setUp(self):
        self.p = VentureScriptParser.instance()
        self.expression = self.p.instruction


    def test_assume(self):
        # Assume
        #
        self.run_test( "assuMe blah = moo",
                [{"loc": j(0,6,7,4,12,1,14,3), "value":{
                    "instruction" : {"loc": j(0,6), "value":"assume"},
                    "symbol" : {"loc": j(7,4), "value":"blah"},
                    "expression" : {"loc": j(14,3), "value":"moo"},
                    }}])

    def test_labeled_assume(self):
        self.run_test( "name : assume a = b",
                [{"loc":j(0,4,5,1,7,6,14,1,16,1,18,1), "value":{
                    "instruction" : {"loc":j(7,6), "value":"labeled_assume"},
                    "symbol" : {"loc": j(14,1), "value":"a"},
                    "expression" : {"loc":j(18,1), "value":"b"},
                    "label" : {"loc":j(0,4), "value":'name'},
                    }}])

    def test_predict(self):
        # Predict
        #
        self.run_test( "  prediCt blah",
                [{"loc":j(2,7,10,4), "value":{
                    "instruction" : {"loc":j(2,7), "value":"predict"},
                    "expression" : {"loc":j(10,4), "value":"blah"},
                    }}])
    def test_labeled_predict(self):
        self.run_test( "name : predict blah",
                [{"loc":j(0,4,5,1,7,7,15,4), "value":{
                    "instruction" : {"loc":j(7,7), "value":"labeled_predict"},
                    "expression" : {"loc":j(15,4), "value":"blah"},
                    "label" : {"loc":j(0,4), "value":'name'},
                    }}])

    def test_observe(self):
        # Observe
        #
        self.run_test( "obServe blah = 1.3",
                [{"loc":j(0,7,8,4,13,1,15,3), "value":{
                    "instruction" : {"loc":j(0,7), "value":"observe"},
                    "expression" : {"loc":j(8,4), "value":"blah"},
                    "value" : {"loc": j(15,3), "value":v.number(1.3)},
                    }}])
    def test_labeled_observe(self):
        self.run_test( "name : observe a = count<32>",
                [{"loc":j(0,4,5,1,7,7,15,1,17,1,19,9), "value":{
                    "instruction" : {"loc":j(7,7), "value":"labeled_observe"},
                    "expression" : {"loc":j(15,1), "value":"a"},
                    "value" : {"loc":j(19,9), "value":{'type':'count', 'value':32.0}},
                    "label" : {"loc":j(0,4), "value":'name'},
                    }}])

    def test_forget(self):
        # Forget
        #
        self.run_test( "FORGET 34",
                [{"loc":j(0,6,7,2), "value":{
                    "instruction" : {"loc":j(0,6), "value":"forget"},
                    "directive_id" : {"loc":j(7,2), "value":34},
                    }}])

    def test_labeled_forget(self):
        self.run_test( "forget blah",
                [{"loc":j(0,6,7,4), "value":{
                    "instruction" : {"loc":j(0,6), "value":"labeled_forget"},
                    "label" : {"loc":j(7,4), "value":"blah"},
                    }}])

    def test_sample(self):
        # Sample
        #
        self.run_test( "saMple blah",
                [{"loc":j(0,6,7,4), "value":{
                    "instruction" : {"loc":j(0,6), "value":"sample"},
                    "expression" : {"loc":j(7,4), "value":"blah"},
                    }}])

    def test_force(self):
        # Force
        #
        self.run_test( "force blah = count<132>",
                [{"loc":j(0,5,6,4,11,1,13,10), "value":{
                    "instruction" : {"loc":j(0,5), "value":"force"},
                    "expression" : {"loc":j(6,4), "value":"blah"},
                    "value" : {"loc":j(13,10), "value":{'type':'count', 'value':132.0}},
                    }}])

    def test_infer(self):
        # Infer
        #
        self.run_test( " infer 132",
                [{"loc":j(1,5,7,3), "value":{
                    "instruction" : {"loc":j(1,5), "value":"infer"},
                    "expression" : {"loc":j(7,3), "value":v.number(132.0)},
                    }}])

    def test_program(self):
        self.expression = self.p.program
        self.run_test( "force blah = count<132> infer 132",
                [{"loc":j(0,5,6,4,11,1,13,10,24,5,30,3), "value":[
                    {"loc":j(0,5,6,4,11,1,13,10), "value":{
                        "instruction" : {"loc":j(0,5), "value":"force"},
                        "expression" : {"loc":j(6,4), "value":"blah"},
                        "value" : {"loc":j(13,10), "value":{'type':'count', 'value':132.0}},
                        }},{"loc":j(24,5,30,3), "value":{
                        "instruction" : {"loc":j(24,5), "value":"infer"},
                        "expression" : {"loc":j(30,3), "value":v.number(132.0)},
                    }}]}])



