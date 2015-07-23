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
from nose.plugins.attrib import attr
import unittest

from venture.exception import VentureException
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

    def test_collapse_identity(self):
        # '((a+b))'
        a = {'loc':[0,6],'value':[
                {'loc':[0,6], 'value':v.sym('identity')},
                {'loc':[1,5], 'value':[
                    {'loc':[1,5], 'value':v.sym('identity')},
                    {'loc':[2,4], 'value':[
                        {'loc':[2,2], 'value':v.sym('+')},
                        {'loc':[3,3], 'value':'a'},
                        {'loc':[4,4], 'value':'b'},
                        ]}
                    ]}
                ]}
        b = {'loc':[0,6],'value':[
                {'loc':[0,6], 'value':v.sym('identity')},
                {'loc':[1,5], 'value':[
                    {'loc':[2,2], 'value':v.sym('+')},
                    {'loc':[3,3], 'value':'a'},
                    {'loc':[4,4], 'value':'b'},
                    ]}
                ]}
        output = module._collapse_identity(a,('+'))
        self.assertEqual(output,b)
        # ' a+b'
        a = {'loc':[1,3], 'value':[
                {'loc':[1,1], 'value':v.sym('+')},
                {'loc':[2,2], 'value':'a'},
                {'loc':[3,3], 'value':'b'},
                ]}
        output = module._collapse_identity(a,('+'))
        self.assertEqual(output,a)
        # ' (a)'
        a = {'loc':[1,3], 'value':[
                {'loc':[1,3], 'value':v.sym('identity')},
                {'loc':[2,2], 'value':'a'},
                ]}
        output = module._collapse_identity(a,('+'))
        self.assertEqual(output,a)
        # ' a'
        a = {'loc':[1,1], 'value':'a'}
        output = module._collapse_identity(a,('+'))
        self.assertEqual(output,a)

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
                r(0,7,r(0,7,v.sym('identity'),1,5,r(1,5,v.sym('let'),1,3,r(1,3,r(1,1,v.sym('a'),3,1,v.sym('b'))),5,1,v.sym('c')))))

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
                r(0,3,r(0,3,v.sym('identity'),1,1,v.sym('a'))))


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
                r(0,7,r(1,1,v.sym('add'),0,1,v.sym('a'),2,5,r(2,5,v.sym('identity'),3,3,r(4,1,v.sym('add'),3,1,v.sym('b'),5,1,v.sym('c')))))
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
                    [[[v.sym('identity'), [v.sym(y), v.sym('a'), v.sym('b')]]]],
                    'fn_application')
        self.run_legacy_test( '((a+b))()',
                [[[v.sym('identity'), [v.sym('identity'), [v.sym('add'), v.sym('a'), v.sym('b')]]]]],
                'fn_application')


    def test_the_rest_of_the_shizzle(self):
        self.run_legacy_test( 'a**b**c',
                [[v.sym('pow'), v.sym('a'), [v.sym('pow'), v.sym('b'), v.sym('c')]]],
                'exponent')
        self.run_legacy_test( 'a**(b**c)',
                [[v.sym('pow'), v.sym('a'), [v.sym('identity'), [v.sym('pow'), v.sym('b'), v.sym('c')]]]],
                'exponent')
        self.run_legacy_test( '(a**b)**c',
                [[v.sym('pow'), [v.sym('identity'), [v.sym('pow'), v.sym('a'), v.sym('b')]], v.sym('c')]],
                'exponent')
        self.run_legacy_test( '((a**b))**c',
                [[v.sym('pow'), [v.sym('identity'), [v.sym('identity'), [v.sym('pow'), v.sym('a'), v.sym('b')]]], v.sym('c')]],
                'exponent')
        for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + equality_ops + add_sub_ops + mul_div_ops:
            self.run_legacy_test( '(a ' + x + ' b)**c',
                    [[v.sym('pow'),[v.sym('identity'), [v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
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
                [[v.sym('div'),[v.sym('identity'), [v.sym('mul'), v.sym('a'), v.sym('b')]], v.sym('c')]],
                'mul_div')
        self.run_legacy_test( '(a/b)*c',
                [[v.sym('mul'),[v.sym('identity'), [v.sym('div'), v.sym('a'), v.sym('b')]], v.sym('c')]],
                'mul_div')
        self.run_legacy_test( 'a*(b/c)',
                [[v.sym('mul'), v.sym('a'), [v.sym('identity'), [v.sym('div'), v.sym('b'), v.sym('c')]]]],
                'mul_div')
        self.run_legacy_test( 'a/(b*c)',
                [[v.sym('div'), v.sym('a'), [v.sym('identity'), [v.sym('mul'), v.sym('b'), v.sym('c')]]]],
                'mul_div')
        self.run_legacy_test( 'a/((b/c))',
                [[v.sym('div'), v.sym('a'), [v.sym('identity'), [v.sym('identity'), [v.sym('div'), v.sym('b'), v.sym('c')]]]]],
                'mul_div')
        self.run_legacy_test( 'a*(((b*c)))',
                [[v.sym('mul'), v.sym('a'), [v.sym('identity'), [v.sym('identity'), [v.sym('identity'), [v.sym('mul'), v.sym('b'), v.sym('c')]]]]]],
                'mul_div')
        # Test that mul_div has medium precedence
        for x, y in exponent_ops:
            self.run_legacy_test( 'a' + x + 'b*c',
                    [[v.sym('mul'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'mul_div')
        for x, y in boolean_and_ops + boolean_or_ops + equality_ops + comparison_ops + add_sub_ops:
            self.run_legacy_test( '(a ' + x + ' b)*c',
                    [[v.sym('mul'), [v.sym('identity'), [v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'mul_div')
        for x, y in exponent_ops:
            self.run_legacy_test( '(a' + x + 'b)*c',
                    [[v.sym('mul'),[v.sym('identity'),[v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
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
                [[v.sym('sub'),[v.sym('identity'), [v.sym('add'), v.sym('a'), v.sym('b')]], v.sym('c')]],
                'add_sub')
        self.run_legacy_test( '(a-b)+c',
                [[v.sym('add'),[v.sym('identity'), [v.sym('sub'), v.sym('a'), v.sym('b')]], v.sym('c')]],
                'add_sub')
        self.run_legacy_test( 'a+(b-c)',
                [[v.sym('add'), v.sym('a'), [v.sym('identity'), [v.sym('sub'), v.sym('b'), v.sym('c')]]]],
                'add_sub')
        self.run_legacy_test( 'a-(b+c)',
                [[v.sym('sub'), v.sym('a'), [v.sym('identity'), [v.sym('add'), v.sym('b'), v.sym('c')]]]],
                'add_sub')
        self.run_legacy_test( 'a-((b-c))',
                [[v.sym('sub'), v.sym('a'), [v.sym('identity'), [v.sym('identity'), [v.sym('sub'), v.sym('b'), v.sym('c')]]]]],
                'add_sub')
        self.run_legacy_test( 'a+(((b+c)))',
                [[v.sym('add'), v.sym('a'), [v.sym('identity'), [v.sym('identity'), [v.sym('identity'), [v.sym('add'), v.sym('b'), v.sym('c')]]]]]],
                'add_sub')
        # Test that add_sub has medium precedence
        for x, y in exponent_ops + mul_div_ops:
            self.run_legacy_test( 'a' + x + 'b+c',
                    [[v.sym('add'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'add_sub')
        for x, y in boolean_and_ops + boolean_or_ops + equality_ops + comparison_ops:
            self.run_legacy_test( '(a ' + x + ' b)+c',
                    [[v.sym('add'), [v.sym('identity'), [v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'add_sub')
        # Don't collapse identities with greater precedence
        for x, y in exponent_ops + mul_div_ops:
            self.run_legacy_test( '(a' + x + 'b)+c',
                    [[v.sym('add'),[v.sym('identity'),[v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
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
                    [[v.sym('lt'), [v.sym('identity'), [v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'comparison')
        for x, y in mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( '(a' + x + 'b) < c',
                    [[v.sym('lt'),[v.sym('identity'),[v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'comparison')
        self.run_legacy_test( '(a > b) < (c > d)',
                [[v.sym('lt'),[v.sym('identity'),[v.sym('gt'), v.sym('a'), v.sym('b')]], [v.sym('identity'), [v.sym('gt'), v.sym('c'), v.sym('d')]]]],
                'comparison')
        self.run_legacy_test( 'a < ((b > c))',
                [[v.sym('lt'), v.sym('a'), [v.sym('identity'), [v.sym('identity'), [v.sym('gt'), v.sym('b'), v.sym('c')]]]]],
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
                    [[v.sym('eq'), [v.sym('identity'), [v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'equality')
        for x, y in mul_div_ops + exponent_ops + add_sub_ops + comparison_ops:
            self.run_legacy_test( '(a ' + x + ' b)==c',
                    [[v.sym('eq'),[v.sym('identity'),[v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'equality')
        self.run_legacy_test( '(a!=b)==(c!=d)',
                [[v.sym('eq'),[v.sym('identity'),[v.sym('neq'), v.sym('a'), v.sym('b')]], [v.sym('identity'), [v.sym('neq'), v.sym('c'), v.sym('d')]]]],
                'equality')
        self.run_legacy_test( 'a==((b!=c))',
                [[v.sym('eq'), v.sym('a'), [v.sym('identity'), [v.sym('identity'), [v.sym('neq'), v.sym('b'), v.sym('c')]]]]],
                'equality')


        # And
        #
        self.run_legacy_test( 'a && b && c',
                [[v.sym('and'), [v.sym('and'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'boolean_and')
        self.run_legacy_test( '(a&&b)&&c',
                [[v.sym('and'), [v.sym('identity'), [v.sym('and'), v.sym('a'), v.sym('b')]], v.sym('c')]],
                'boolean_and')
        self.run_legacy_test( 'a&&(b&&c)',
                [[v.sym('and'), v.sym('a'), [v.sym('identity'), [v.sym('and'), v.sym('b'), v.sym('c')]]]],
                'boolean_and')
        self.run_legacy_test( 'a&&((b&&c))',
                [[v.sym('and'), v.sym('a'), [v.sym('identity'), [v.sym('identity'), [v.sym('and'), v.sym('b'), v.sym('c')]]]]],
                'boolean_and')
        # Test that and has low precedence
        for x, y in comparison_ops + equality_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( 'a ' + x + ' b&&c',
                    [[v.sym('and'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'boolean_and')
        for x, y in boolean_or_ops:
            self.run_legacy_test( '(a' + x + 'b)&&c',
                    [[v.sym('and'), [v.sym('identity'), [v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'boolean_and')
        for x, y in comparison_ops + equality_ops + mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( '(a ' + x + ' b)&&c',
                    [[v.sym('and'),[v.sym('identity'),[v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'boolean_and')

        # Or
        #
        self.run_legacy_test( 'a || b || c',
                [[v.sym('or'), [v.sym('or'), v.sym('a'), v.sym('b')], v.sym('c')]],
                'boolean_or')
        self.run_legacy_test( '(a||b)||c',
                [[v.sym('or'), [v.sym('identity'), [v.sym('or'), v.sym('a'), v.sym('b')]], v.sym('c')]],
                'boolean_or')
        self.run_legacy_test( 'a||(b||c)',
                [[v.sym('or'), v.sym('a'), [v.sym('identity'), [v.sym('or'), v.sym('b'), v.sym('c')]]]],
                'boolean_or')
        self.run_legacy_test( 'a||((b||c))',
                [[v.sym('or'), v.sym('a'), [v.sym('identity'), [v.sym('identity'), [v.sym('or'), v.sym('b'), v.sym('c')]]]]],
                'boolean_or')
        # Test that or has low precedence
        for x, y in comparison_ops + equality_ops + add_sub_ops + mul_div_ops + exponent_ops:
            self.run_legacy_test( 'a ' + x + ' b||c',
                    [[v.sym('or'), [v.sym(y), v.sym('a'), v.sym('b')], v.sym('c')]],
                    'boolean_or')
        for x, y in comparison_ops + equality_ops + mul_div_ops + exponent_ops + add_sub_ops:
            self.run_legacy_test( '(a ' + x + ' b)||c',
                    [[v.sym('or'),[v.sym('identity'),[v.sym(y), v.sym('a'), v.sym('b')]], v.sym('c')]],
                    'boolean_or')


        # Expression
        #
        #identity
        self.run_legacy_test( '(a)',
                [[v.symbol('identity'), v.sym('a')]],
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
                                [v.sym('div'),[v.sym('identity'), [v.sym('add'),v.number(1.0),v.number(4.0)]],[v.sym('pow'),v.number(3.0),v.number(5.11)]],
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
        expected = {'instruction':'assume', 'symbol':v.sym('a'), 'expression':[v.sym('b'),v.sym('c'),v.sym('d')]}
        self.assertEqual(output,expected)

    def test_split_program(self):
        output = self.p.split_program(' force blah = count<132>;infer 132')
        instructions = ['force blah = count<132>','infer 132']
        indices = [[1,23],[25,33]]
        self.assertEqual(output,[instructions, indices])

    def test_split_instruction(self):
        output = self.p.split_instruction(' force blah = count<132>')
        indices = {
                'instruction': [1,5],
                'expression': [7,10],
                'value': [14,23],
                }
        strings = {
                'instruction': 'force',
                'expression': 'blah',
                'value': 'count<132>',
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


    def test_character_index_to_expression_index(self):
        # '(a b (c (d e) f ))'
        s = 'a( b,c(d(e),f))'
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
        self.assertEqual(module.parse_instructions(string), expected)
    run_test.__test__ = False

    def test_assume(self):
        # Assume
        #
        self.run_test( 'assuMe blah = moo',
                [{'loc': j(0,6,7,4,12,1,14,3), 'value':{
                    'instruction' : {'loc': j(0,6), 'value':'assume'},
                    'symbol' : {'loc': j(7,4), 'value':v.sym('blah')},
                    'expression' : {'loc': j(14,3), 'value':v.sym('moo')},
                    }}])

    def test_labeled_assume(self):
        self.run_test( 'name : assume a = b',
                [{'loc':j(0,4,5,1,7,6,14,1,16,1,18,1), 'value':{
                    'instruction' : {'loc':j(7,6), 'value':'labeled_assume'},
                    'symbol' : {'loc': j(14,1), 'value':v.sym('a')},
                    'expression' : {'loc':j(18,1), 'value':v.sym('b')},
                    'label' : {'loc':j(0,4), 'value':v.sym('name')},
                    }}])

    def test_predict(self):
        # Predict
        #
        self.run_test( '  prediCt blah',
                [{'loc':j(2,7,10,4), 'value':{
                    'instruction' : {'loc':j(2,7), 'value':'predict'},
                    'expression' : {'loc':j(10,4), 'value':v.sym('blah')},
                    }}])
    def test_labeled_predict(self):
        self.run_test( 'name : predict blah',
                [{'loc':j(0,4,5,1,7,7,15,4), 'value':{
                    'instruction' : {'loc':j(7,7), 'value':'labeled_predict'},
                    'expression' : {'loc':j(15,4), 'value':v.sym('blah')},
                    'label' : {'loc':j(0,4), 'value':v.sym('name')},
                    }}])

    def test_observe(self):
        # Observe
        #
        self.run_test( 'obServe blah = 1.3',
                [{'loc':j(0,7,8,4,13,1,15,3), 'value':{
                    'instruction' : {'loc':j(0,7), 'value':'observe'},
                    'expression' : {'loc':j(8,4), 'value':v.sym('blah')},
                    'value' : {'loc': j(15,3), 'value':v.number(1.3)},
                    }}])
    def test_labeled_observe(self):
        self.run_test( 'name : observe a = count<32>',
                [{'loc':j(0,4,5,1,7,7,15,1,17,1,19,9), 'value':{
                    'instruction' : {'loc':j(7,7), 'value':'labeled_observe'},
                    'expression' : {'loc':j(15,1), 'value':v.sym('a')},
                    'value' : {'loc':j(19,9), 'value':{'type':'count', 'value':32.0}},
                    'label' : {'loc':j(0,4), 'value':v.sym('name')},
                    }}])

    def test_forget(self):
        # Forget
        #
        self.run_test( 'FORGET 34',
                [{'loc':j(0,6,7,2), 'value':{
                    'instruction' : {'loc':j(0,6), 'value':'forget'},
                    'directive_id' : {'loc':j(7,2), 'value':34},
                    }}])

    def test_labeled_forget(self):
        self.run_test( 'forget blah',
                [{'loc':j(0,6,7,4), 'value':{
                    'instruction' : {'loc':j(0,6), 'value':'labeled_forget'},
                    'label' : {'loc':j(7,4), 'value':v.sym('blah')},
                    }}])

    def test_sample(self):
        # Sample
        #
        self.run_test( 'saMple blah',
                [{'loc':j(0,6,7,4), 'value':{
                    'instruction' : {'loc':j(0,6), 'value':'sample'},
                    'expression' : {'loc':j(7,4), 'value':v.sym('blah')},
                    }}])

    def test_force(self):
        # Force
        #
        self.run_test( 'force blah = count<132>',
                [{'loc':j(0,5,6,4,11,1,13,10), 'value':{
                    'instruction' : {'loc':j(0,5), 'value':'force'},
                    'expression' : {'loc':j(6,4), 'value':v.sym('blah')},
                    'value' : {'loc':j(13,10), 'value':{'type':'count', 'value':132.0}},
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
        self.run_test( 'force blah = count<132>;infer 132',
                [{'loc':j(0,5,6,4,11,1,13,10), 'value':{
                        'instruction' : {'loc':j(0,5), 'value':'force'},
                        'expression' : {'loc':j(6,4), 'value':v.sym('blah')},
                        'value' : {'loc':j(13,10), 'value':{'type':'count', 'value':132.0}},
                        }},{'loc':j(24,5,30,3), 'value':{
                        'instruction' : {'loc':j(24,5), 'value':'infer'},
                        'expression' : {'loc':j(30,3), 'value':v.number(132.0)},
                    }}])

def testPunctuationTermination():
    assert module.string_complete_p("plot('aaoeu', aoeu)")
