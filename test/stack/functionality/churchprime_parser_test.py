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
import venture.value.dicts as v
import venture.test.errors as err

# Almost the same effect as @venture.test.config.in_backend('none'),
# but works on the whole class
@attr(backend='none')
class TestChurchPrimeParser(unittest.TestCase):
    _multiprocess_can_split_ = True
    def setUp(self):
        self.p = ChurchPrimeParser.instance()
        self.expression = None

    def test_expression(self):
        with self.assertRaises(VentureException):
            self.p.parse_locexpression('')
        self.assertEqual(self.p.parse_locexpression('(a b (c number<1>))'),
                {'loc': [0,18], 'value':[
                    {'loc': [1,1], 'value': v.sym('a')},
                    {'loc': [3,3], 'value': v.sym('b')},
                    {'loc': [5,17], 'value': [
                        {'loc': [6,6], 'value': v.sym('c')},
                        {'loc': [8,16], 'value': v.number(1.0)}]}]})

    def test_parse_instruction(self):
        output = self.p.parse_instruction('[assume a (b c d)]')
        expected = {'instruction':'evaluate',
                    'expression':[v.sym('assume'), v.sym('a'),
                                  [v.sym('b'), v.sym('c'), v.sym('d')]]}
        self.assertEqual(output,expected)

    def test_parse_assume_values(self):
        output = self.p.parse_instruction("[assume_values (a b) c  ]")
	
        expected = {'instruction':'evaluate',
                    'expression':[v.sym('assume_values'), [v.sym('a'),
		    v.sym('b')], v.sym('c')]}
        self.assertEqual(output,expected)

    def test_parse_assume_values_empty(self):
      self.assertEqual(self.p.parse_instruction("[assume_values ( ) c  ]"),
          {'instruction': 'evaluate', 
            'expression': [
                      {'type': 'symbol', 'value': 'assume_values'},
                      [],
                      {'type': 'symbol', 'value': 'c'}]}
        )

    def test_assume_values_loc(self):
      with self.assertRaises(VentureException):
          self.p.parse_locexpression('')
      self.assertEqual(self.p.parse_locexpression("[assume_values (a b) c  ]"),
        {'loc': [1, 21], 'value': [
          {'loc': [1, 13], 'value': {'type': 'symbol', 'value': 'assume_values'}},
          {'loc': [15, 19], 'value': [
            {'loc': [16, 16], 'value': {'type': 'symbol', 'value': 'a'}},
            {'loc': [18, 18], 'value': {'type': 'symbol', 'value': 'b'}}]},
          {'loc': [21, 21], 'value': {'type': 'symbol', 'value': 'c'}}]}
        )



    def test_parse_and_unparse_instruction(self):
        def round_tripped(inst):
            return self.p.unparse_instruction(self.p.parse_instruction(inst))
        self.assertEqual(round_tripped('[assume a (b c d)]'),
                         '(assume a (b c d))')
        self.assertEqual(round_tripped('foo: [assume a (b c d)]'),
                         '(assume a (b c d) foo)')

    # detects bug where '>=' is parsed as '> =' (because '>' is its own symbol)
    def test_double_symbol(self):
        output = self.p.parse_instruction('[predict (>= 1 1)]')
        expected = {
            'expression': [v.symbol('predict'),
                           [v.symbol('gte'), v.number(1.0), v.number(1.0)]],
            'instruction': 'evaluate'}
        self.assertEqual(output, expected)

    # detects bug parsing lambda expressions with no arguments
    def test_empty_lambda(self):
        output = self.p.parse_instruction('[predict (lambda () 0)]')
        expected = {'instruction': 'evaluate',
                    'expression': [v.symbol('predict'),
                                   [v.symbol('lambda'), [], v.number(0.0)]]}
        self.assertEqual(output, expected)

    def test_split_instruction(self):
        output = self.p.split_instruction(' [define blah count<132> ]')
        print output
        indices = {
                'instruction': [2,7],
                'symbol': [9,12],
                'expression': [14,23],
                }
        strings = {
                'instruction': 'define',
                'symbol': 'blah',
                'expression': 'count<132>',
                }
        self.assertEqual(output,[strings,indices])

    def test_expression_index_to_text_index(self):
        s = '(a b (c (d e) f ))'
        f = self.p.expression_index_to_text_index
        output = f(s, [0])
        self.assertEqual(output, [1,1])
        output = f(s, [2])
        self.assertEqual(output, [5,16])
        output = f(s, [2,0])
        self.assertEqual(output, [6,6])
        output = f(s, [2,1,1])
        self.assertEqual(output, [11,11])


    def test_mark_up_expression_smoke(self):
        parsed = self.p.parse_expression('(add 2 3)')
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
