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
# -*- coding: utf-8 -*-

import unittest

from nose.plugins.attrib import attr

from venture.parser import VentureScriptParser
import venture.parser.venture_script.parse as module
import venture.value.dicts as v

exponent_ops = [('**','pow')]
add_sub_ops = [('+', 'add'), ('-','sub')]
mul_div_ops = [('*','mul'), ('/','div')]
comparison_ops = [('<=', 'lte'), ('>=', 'gte'), ('<', 'lt'),('>', 'gt')]
equality_ops = [('==','eq'),('!=', 'neq')]
boolean_and_ops = [('&&', 'and')]
boolean_or_ops = [('||','or')]

def r(*args):
    return [{'loc':[a,a+b-1], 'value':c} for a,b,c in zip(*(iter(args),)*3)]

def j(*args):
    mins = []
    maxes = []
    # This kooky expression traverses the args list by pairs.  How?
    # Zipping a mutable iterator with itself.  See
    # http://stackoverflow.com/questions/4628290/pairs-from-single-list
    # for an in-depth discussion.
    for a, b in zip(*(iter(args),)*2):
        mins.append(a)
        maxes.append(a+b-1)
    return [min(mins), max(maxes)]


# Almost the same effect as @venture.test.config.in_backend('none'),
# but works on the whole class
@attr(backend='none')
class TestVentureScriptParserAtoms(unittest.TestCase):
    _multiprocess_can_split_ = True

    def setUp(self):
        self.p = VentureScriptParser.instance()

    def run_test(self, string, expected):
        self.maxDiff = None
        self.assertEqual([self.p.parse_locexpression(string)], expected)
    run_test.__test__ = False

    def run_legacy_test(self, string, expected, _name):
        self.maxDiff = None
        self.assertEqual([self.p.parse_expression(string)], expected)
    run_legacy_test.__test__ = False

    def test_optional_let(self):
        self.run_test( 'a',
                r(0,1,v.sym('a')))
        self.run_test( '(a=b;c)',
                r(0,7,r(1,5,v.sym('let'),1,3,r(1,3,r(1,1,v.sym('a'),3,1,v.sym('b'))),5,1,v.sym('c'))))

    def test_proc(self):
        self.run_test( 'proc(arg, arg){ true }',
                r(0,22,r(0,4,v.sym('lambda'),4,10,r(5,3,v.sym('arg'),10,3,v.sym('arg')),16,4,v.boolean(True))))
        self.run_test( 'proc(){ a=b;c }',
                r(0,15,r(0,4,v.sym('lambda'),4,2,r(),8,5,r(8,5,v.sym('let'),8,3,r(8,3,r(8,1,v.sym('a'),10,1,v.sym('b'))),12,1,v.sym('c')))))


    def test_let(self):
        self.run_test( '{ a=b;c=d;e}',
                r(0,12,r(0,12,v.sym('let'),2,7,r(2,3,r(2,1,v.sym('a'),4,1,v.sym('b')),6,3,r(6,1,v.sym('c'),8,1,v.sym('d'))),10,1,v.sym('e'))))


    def test_identity(self):
        self.run_test( '(a)',
                r(0,3,v.sym('a')))


    def test_if_else(self):
        self.run_test( 'if (a) { b }else {c}',
                r(0,20,r(0,2,v.sym('if'),4,1,v.sym('a'),9,1,v.sym('b'),18,1,v.sym('c'))))
        self.run_test( 'if( a=b;c) {d=e;f}else{g=h;i }',
                r(0,30,r(0,2,v.sym('if'),
                    4,5,r(4,5,v.sym('let'),4,3,r(4,3,r(4,1,v.sym('a'),6,1,v.sym('b'))),8,1,v.sym('c')),
                         12,5,r(12,5,v.sym('let'),12,3,r(12,3,r(12,1,v.sym('d'),14,1,v.sym('e'))),16,1,v.sym('f')),
                         23,5,r(23,5,v.sym('let'),23,3,r(23,3,r(23,1,v.sym('g'),25,1,v.sym('h'))),27,1,v.sym('i')),
                )))

    def test_infix_locations(self):
        self.run_test( 'a+(b+c)',
                r(0,7,r(1,1,v.sym('add'),0,1,v.sym('a'),2,5,r(4,1,v.sym('add'),3,1,v.sym('b'),5,1,v.sym('c'))))
                )


    # I'm not going to bother augmenting all of the
    # previous tests to include line numbers etc.
    # Instead, use a different test handler

    def test_function_application(self):
        self.run_legacy_test( 'a(b)(c)',
                [[[v.sym('a'), v.sym('b')], v.sym('c')]],
                'fn_application')
        self.run_legacy_test( 'a(b, c)',
                [[v.sym('a'), v.sym('b'), v.sym('c')]],
                'fn_application')
        self.run_legacy_test( 'a()',
                [[v.sym('a')]],
                'fn_application')
        # Function application has precedence over all infix operators
        for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( 'a ' + x + ' b()',
                    [[v.sym(y), v.sym('a'), [v.sym('b')]]],
                    'expression')
        for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( '(a ' + x + ' b)()',
                    [[[v.sym(y), v.sym('a'), v.sym('b')]]],
                    'fn_application')
        self.run_legacy_test( '((a+b))()',
                [[[v.sym('add'), v.sym('a'), v.sym('b')]]],
                'fn_application')


    def test_the_rest_of_the_shizzle(self):
        self.run_legacy_test( 'a**b**c',
                [[v.sym('pow'), v.sym('a'), [v.sym('pow'), v.sym('b'), v.sym('c')]]],
                'exponent')
        self.run_legacy_test( 'a**(b**c)',
                [[v.sym('pow'), v.sym('a'), [v.sym('pow'), v.sym('b'), v.sym('c')]]],
                'exponent')
        self.run_legacy_test( '(a**b)**c',
                [[v.sym('pow'), [v.sym('pow'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'exponent')
        self.run_legacy_test( '((a**b))**c',
                [[v.sym('pow'), [v.sym('pow'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'exponent')
        for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + equality_ops + add_sub_ops + mul_div_ops:
            self.run_legacy_test( '(a ' + x + ' b)**c',
                    [[v.sym('pow'),[v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'exponent')



        # Multiplication and division
        #
        self.run_legacy_test( 'a*b/c',
                [[v.sym('div'),[v.sym('mul'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'mul_div')
        self.run_legacy_test( 'a/b*c',
                [[v.sym('mul'),[v.sym('div'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'mul_div')
        # Don't collapse redundant identities
        self.run_legacy_test( '(a*b)/c',
                [[v.sym('div'),[v.sym('mul'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'mul_div')
        self.run_legacy_test( '(a/b)*c',
                [[v.sym('mul'),[v.sym('div'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'mul_div')
        self.run_legacy_test( 'a*(b/c)',
                [[v.sym('mul'), v.sym('a'), [v.sym('div'), v.sym('b'), v.sym('c')]]],
                'mul_div')
        self.run_legacy_test( 'a/(b*c)',
                [[v.sym('div'), v.sym('a'), [v.sym('mul'), v.sym('b'), v.sym('c')]]],
                'mul_div')
        self.run_legacy_test( 'a/((b/c))',
                [[v.sym('div'), v.sym('a'), [v.sym('div'), v.sym('b'), v.sym('c')]]],
                'mul_div')
        self.run_legacy_test( 'a*(((b*c)))',
                [[v.sym('mul'), v.sym('a'), [v.sym('mul'), v.sym('b'), v.sym('c')]]],
                'mul_div')
        # Test that mul_div has medium precedence
        for x, y in exponent_ops:
            self.run_legacy_test( 'a' + x + 'b*c',
                    [[v.sym('mul'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'mul_div')
        for x, y in boolean_and_ops + boolean_or_ops + equality_ops + comparison_ops + add_sub_ops:
            self.run_legacy_test( '(a ' + x + ' b)*c',
                    [[v.sym('mul'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'mul_div')
        for x, y in exponent_ops:
            self.run_legacy_test( '(a' + x + 'b)*c',
                    [[v.sym('mul'),[v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'mul_div')



        # Addition and subtraction
        #
        self.run_legacy_test( 'a+b-c',
                [[v.sym('sub'),[v.sym('add'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'add_sub')
        self.run_legacy_test( 'a-b+c',
                [[v.sym('add'),[v.sym('sub'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'add_sub')
        self.run_legacy_test( '(a+b)-c',
                [[v.sym('sub'),[v.sym('add'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'add_sub')
        self.run_legacy_test( '(a-b)+c',
                [[v.sym('add'),[v.sym('sub'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'add_sub')
        self.run_legacy_test( 'a+(b-c)',
                [[v.sym('add'), v.sym('a'), [v.sym('sub'), v.sym('b'), v.sym('c')]]],
                'add_sub')
        self.run_legacy_test( 'a-(b+c)',
                [[v.sym('sub'), v.sym('a'), [v.sym('add'), v.sym('b'), v.sym('c')]]],
                'add_sub')
        self.run_legacy_test( 'a-((b-c))',
                [[v.sym('sub'), v.sym('a'), [v.sym('sub'), v.sym('b'), v.sym('c')]]],
                'add_sub')
        self.run_legacy_test( 'a+(((b+c)))',
                [[v.sym('add'), v.sym('a'), [v.sym('add'), v.sym('b'), v.sym('c')]]],
                'add_sub')
        # Test that add_sub has medium precedence
        for x, y in exponent_ops + mul_div_ops:
            self.run_legacy_test( 'a' + x + 'b+c',
                    [[v.sym('add'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'add_sub')
        for x, y in boolean_and_ops + boolean_or_ops + equality_ops + comparison_ops:
            self.run_legacy_test( '(a ' + x + ' b)+c',
                    [[v.sym('add'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'add_sub')
        # Don't collapse identities with greater precedence
        for x, y in exponent_ops + mul_div_ops:
            self.run_legacy_test( '(a' + x + 'b)+c',
                    [[v.sym('add'),[v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'add_sub')

        # Comparison
        #
        self.run_legacy_test( 'a < b < c',
                [[v.sym('lt'),[v.sym('lt'), v.sym('a'), v.sym('b')],v.sym('c')]],
                'comparison')
        # Test all operators
        for x, y in comparison_ops:
            self.run_legacy_test( 'a ' + x + ' b',
                    [[v.sym(y), v.sym('a'), v.sym('b')]],
                    'comparison')
        # Test that comparison has low precedence
        for x, y in add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( 'a' + x + 'b < c',
                    [[v.sym('lt'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'comparison')
        for x, y in boolean_and_ops + boolean_or_ops + equality_ops:
            self.run_legacy_test( '(a' + x + 'b)<c',
                    [[v.sym('lt'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'comparison')
        for x, y in mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( '(a' + x + 'b) < c',
                    [[v.sym('lt'),[v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'comparison')
        self.run_legacy_test( '(a > b) < (c > d)',
                [[v.sym('lt'),[v.sym('gt'), v.sym('a'), v.sym('b')], [v.sym('gt'), v.sym('c'), v.sym('d')]]],
                'comparison')
        self.run_legacy_test( 'a < ((b > c))',
                [[v.sym('lt'), v.sym('a'), [v.sym('gt'), v.sym('b'), v.sym('c')]]],
                'comparison')

        # Equality
        #
        self.run_legacy_test( 'a==b==c',
                [[v.sym('eq'),[v.sym('eq'), v.sym('a'), v.sym('b')],v.sym('c')]],
                'equality')
        # Test all operators
        for x, y in equality_ops:
            self.run_legacy_test( 'a' + x + 'b',
                    [[v.sym(y), v.sym('a'), v.sym('b')]],
                    'equality')
        # Test that equality has low precedence
        for x, y in add_sub_ops + mul_div_ops + exponent_ops + comparison_ops:
            self.run_legacy_test( 'a ' + x + ' b==c',
                    [[v.sym('eq'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'equality')
        for x, y in boolean_and_ops + boolean_or_ops:
            self.run_legacy_test( '(a' + x + 'b)==c',
                    [[v.sym('eq'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'equality')
        for x, y in mul_div_ops + exponent_ops + add_sub_ops + comparison_ops:
            self.run_legacy_test( '(a ' + x + ' b)==c',
                    [[v.sym('eq'),[v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'equality')
        self.run_legacy_test( '(a!=b)==(c!=d)',
                [[v.sym('eq'),[v.sym('neq'), v.sym('a'), v.sym('b')], [v.sym('neq'), v.sym('c'), v.sym('d')]]],
                'equality')
        self.run_legacy_test( 'a==((b!=c))',
                [[v.sym('eq'), v.sym('a'), [v.sym('neq'), v.sym('b'), v.sym('c')]]],
                'equality')


        # And
        #
        self.run_legacy_test( 'a && b && c',
                [[v.sym('and'), [v.sym('and'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'boolean_and')
        self.run_legacy_test( '(a&&b)&&c',
                [[v.sym('and'), [v.sym('and'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'boolean_and')
        self.run_legacy_test( 'a&&(b&&c)',
                [[v.sym('and'), v.sym('a'), [v.sym('and'), v.sym('b'), v.sym('c')]]],
                'boolean_and')
        self.run_legacy_test( 'a&&((b&&c))',
                [[v.sym('and'), v.sym('a'), [v.sym('and'), v.sym('b'), v.sym('c')]]],
                'boolean_and')
        # Test that and has low precedence
        for x, y in comparison_ops + equality_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( 'a ' + x + ' b&&c',
                    [[v.sym('and'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'boolean_and')
        for x, y in boolean_or_ops:
            self.run_legacy_test( '(a' + x + 'b)&&c',
                    [[v.sym('and'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'boolean_and')
        for x, y in comparison_ops + equality_ops + mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( '(a ' + x + ' b)&&c',
                    [[v.sym('and'),[v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'boolean_and')

        # Or
        #
        self.run_legacy_test( 'a || b || c',
                [[v.sym('or'), [v.sym('or'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'boolean_or')
        self.run_legacy_test( '(a||b)||c',
                [[v.sym('or'), [v.sym('or'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'boolean_or')
        self.run_legacy_test( 'a||(b||c)',
                [[v.sym('or'), v.sym('a'), [v.sym('or'), v.sym('b'), v.sym('c')]]],
                'boolean_or')
        self.run_legacy_test( 'a||((b||c))',
                [[v.sym('or'), v.sym('a'), [v.sym('or'), v.sym('b'), v.sym('c')]]],
                'boolean_or')
        # Test that or has low precedence
        for x, y in comparison_ops + equality_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( 'a ' + x + ' b||c',
                    [[v.sym('or'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'boolean_or')
        for x, y in comparison_ops + equality_ops + mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( '(a ' + x + ' b)||c',
                    [[v.sym('or'),[v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'boolean_or')


        # Expression
        #
        #identity
        self.run_legacy_test( '(a)',
                [v.sym('a')],
                'expression')
        #let
        self.run_legacy_test( '{ a=b; c=d; e}',
                [[v.sym('let'), [[v.sym('a'),v.sym('b')], [v.sym('c'),v.sym('d')]], v.sym('e')]],
                'expression')
        #proc
        self.run_legacy_test( 'proc(){ a=2; b }',
                [[v.sym('lambda'),[],[v.sym('let'),[[v.sym('a'), v.number(2.0)]], v.sym('b')]]],
                'expression')
        #sym
        self.run_legacy_test( 'b',
                [v.sym('b')],
                'expression')
        #literal
        self.run_legacy_test( '3',
                [v.number(3.0)],
                'expression')
        #if_else
        self.run_legacy_test( 'if (a) { b }else {c}',
                [[v.sym('if'), v.sym('a'), v.sym('b'), v.sym('c')]],
                'expression')
        #function application
        self.run_legacy_test( 'a(b)(c)',
                [[[v.sym('a'), v.sym('b')], v.sym('c')]],
                'expression')
        #exponentiation
        self.run_legacy_test( 'a**b**c',
                [[v.sym('pow'), v.sym('a'), [v.sym('pow'), v.sym('b'), v.sym('c')]]],
                'expression')
        #mul_div
        self.run_legacy_test( 'a*b/c',
                [[v.sym('div'),[v.sym('mul'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'expression')
        #add_sub
        self.run_legacy_test( 'a+b-c',
                [[v.sym('sub'),[v.sym('add'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'expression')
        #comparision
        self.run_legacy_test( 'a==b==c',
                [[v.sym('eq'), [v.sym('eq'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'expression')
        #boolean
        self.run_legacy_test( 'true && true || true',
                [[v.sym('or'), [v.sym('and'), v.boolean(True), v.boolean(True)], v.boolean(True)]],
                'expression')


        #fancy expression
        self.run_legacy_test( '''
        (1 + 4)/3**5.11 + 32*4 - 2
        ''',
                [[v.sym('sub'),
                            [v.sym('add'),
                                [v.sym('div'),[v.sym('add'),v.number(1.0),v.number(4.0)],[v.sym('pow'),v.number(3.0),v.number(5.11)]],
                                [v.sym('mul'),v.number(32.0),v.number(4.0)],
                                ],
                            v.number(2.0)]],
                'expression')


# Almost the same effect as @venture.test.config.in_backend('none'),
# but works on the whole class
@attr(backend='none')
class TestVentureScriptParser(unittest.TestCase):
    def setUp(self):
        self.p = VentureScriptParser.instance()

    def test_parse_instruction(self):
        output = self.p.parse_instruction('assume a = b(c,d)')
        expected = {'instruction':'evaluate',
                    'expression':[v.sym('assume'), v.sym('a'),
                                  [v.sym('b'), v.sym('c'), v.sym('d')]]}
        self.assertEqual(output, expected)

    def test_split_program(self):
        output = self.p.split_program(' define blah = count<132>;infer 132')
        instructions = ['define blah = count<132>','infer 132']
        indices = [[1,24],[26,34]]
        self.assertEqual(output,[instructions, indices])

    def test_split_instruction(self):
        output = self.p.split_instruction(' define blah = count<132>')
        indices = {
                'instruction': [1,6],
                'symbol': [8,11],
                'expression': [15,24],
                }
        strings = {
                'instruction': 'define',
                'symbol': 'blah',
                'expression': 'count<132>',
                }
        self.assertEqual(output,[strings,indices])

    def test_expression_index_to_text_index(self):
        # '(a b (c (d e) f ))'
        s = 'a(b,c(d(e),f))'
        f = self.p.expression_index_to_text_index
        output = f(s, [0])
        self.assertEqual(output, [0,0])
        output = f(s, [2])
        self.assertEqual(output, [4,12])
        output = f(s, [2,0])
        self.assertEqual(output, [4,4])
        output = f(s, [2,1,1])
        self.assertEqual(output, [8,8])


    def test_string(self):
        output = self.p.parse_expression('"foo"')
        expected = v.string('foo')
        self.assertEqual(output,expected)


# Almost the same effect as @venture.test.config.in_backend('none'),
# but works on the whole class
@attr(backend='none')
class TestInstructions(unittest.TestCase):
    def setUp(self):
        self.p = VentureScriptParser.instance()

    def run_test(self, string, expected):
        got = module.parse_instructions(string)
        self.assertEqual(got, expected)
    run_test.__test__ = False

    def test_assume(self):
        # Assume
        #
        full_loc = j(0,6,7,4,12,1,14,3)
        self.run_test( 'assuMe blah = moo',
                [{'loc': full_loc, 'value': {
                    'instruction' : {'loc': full_loc, 'value':'evaluate'},
                    'expression' : {'loc': full_loc, 'value':
                        [{'loc': j(0,6), 'value':v.sym('assume')},
                         {'loc': j(7,4), 'value':v.sym('blah')},
                         {'loc': j(14,3), 'value':v.sym('moo')}]},
                    }}])

    def test_labeled_assume(self):
        full_loc = j(0,4,5,1,7,6,14,1,16,1,18,1)
        expr_loc = j(7,6,14,1,16,1,18,1)
        self.run_test( 'name : assume a = b',
                [{'loc':full_loc, 'value':{
                    'instruction' : {'loc': expr_loc, 'value':'evaluate'},
                    'expression' : {'loc': expr_loc, 'value':
                        [{'loc':j(7,6), 'value':v.sym('assume')},
                         {'loc': j(14,1), 'value':v.sym('a')},
                         {'loc':j(18,1), 'value':v.sym('b')},
                         {'loc':j(0,4), 'value':v.sym('name')}]},
                    }}])

    def test_predict(self):
        # Predict
        #
        full_loc = j(2,7,10,4)
        self.run_test( '  prediCt blah',
                [{'loc':full_loc, 'value':{
                    'instruction' : {'loc':full_loc, 'value': 'evaluate'},
                    'expression' : {'loc': full_loc, 'value':
                        [{'loc':j(2,7), 'value':v.sym('predict')},
                         {'loc':j(10,4), 'value':v.sym('blah')}]}
                    }}])
    def test_labeled_predict(self):
        full_loc = j(0,4,5,1,7,7,15,4)
        expr_loc = j(7,7,15,4)
        self.run_test( 'name : predict blah',
                [{'loc':full_loc, 'value':{
                    'instruction' : {'loc':expr_loc, 'value': 'evaluate'},
                    'expression' : {'loc': expr_loc, 'value':
                        [{'loc':j(7,7), 'value':v.sym('predict')},
                         {'loc':j(15,4), 'value':v.sym('blah')},
                         {'loc':j(0,4), 'value':v.sym('name')}]}
                    }}])

    def test_observe(self):
        # Observe
        #
        full_loc = j(0,7,8,4,13,1,15,3)
        self.run_test( 'obServe blah = 1.3',
                [{'loc':full_loc, 'value':{
                    'instruction' : {'loc':full_loc, 'value': 'evaluate'},
                    'expression' : {'loc': full_loc, 'value':
                        [{'loc':j(0,7), 'value':v.sym('observe')},
                         {'loc':j(8,4), 'value':v.sym('blah')},
                         {'loc': j(15,3), 'value':v.number(1.3)}]}
                    }}])
    def test_labeled_observe(self):
        full_loc = j(0,4,5,1,7,7,15,1,17,1,19,9)
        expr_loc = j(7,7,15,1,17,1,19,9)
        self.run_test( 'name : observe a = count<32>',
                [{'loc':full_loc, 'value':{
                    'instruction' : {'loc':expr_loc, 'value': 'evaluate'},
                    'expression' : {'loc':expr_loc, 'value':
                        [{'loc':j(7,7), 'value':v.sym('observe')},
                         {'loc':j(15,1), 'value':v.sym('a')},
                         {'loc':j(19,9), 'value':{'type':'count', 'value':32.0}},
                         {'loc':j(0,4), 'value':v.sym('name')}]}
                    }}])

    def test_infer(self):
        # Infer
        #
        self.run_test( ' infer 132',
                [{'loc':j(1,5,7,3), 'value':{
                    'instruction' : {'loc':j(1,5), 'value':'infer'},
                    'expression' : {'loc':j(7,3), 'value':v.number(132.0)},
                    }}])

    def test_program(self):
        self.run_test( 'define blah = count<132>;infer 132',
                [{'loc':j(0,6,7,4,12,1,14,10), 'value':{
                        'instruction' : {'loc':j(0,6), 'value':'define'},
                        'symbol' : {'loc':j(7,4), 'value':v.sym('blah')},
                        'expression' : {'loc':j(14,10), 'value':{'type':'count', 'value':132.0}},
                        }},{'loc':j(25,5,31,3), 'value':{
                        'instruction' : {'loc':j(25,5), 'value':'infer'},
                        'expression' : {'loc':j(31,3), 'value':v.number(132.0)},
                    }}])

def testPunctuationTermination():
    assert module.string_complete_p("plot('aaoeu', aoeu)")
