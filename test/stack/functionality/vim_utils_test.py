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
from nose.plugins.attrib import attr
import unittest

from venture.exception import VentureException
from venture.sivm import utils

#Note -- these tests only check for minimum functionality

# Almost the same effect as @venture.test.config.in_backend("none"),
# but works on the whole class
@attr(backend="none")
class TestSivmUtils(unittest.TestCase):

    ######################################
    # is_valid_symbol
    ######################################

    def test_is_valid_symbol(self):
        self.assertTrue(utils.is_valid_symbol('abc123'))
        self.assertFalse(utils.is_valid_symbol('123abc'))
        self.assertFalse(utils.is_valid_symbol('+'))
        self.assertFalse(utils.is_valid_symbol(''))

    ######################################
    # desugar_expression
    ######################################

    def test_desugar_expression_if(self):
        a = ['if','a','b',['if','c','d','e']]
        b = [['biplex','a',['lambda',[],'b'],['lambda',[],
                [['biplex','c',['lambda',[],'d'],['lambda',[],'e']]]]]]
        self.assertEqual(utils.desugar_expression(a),b)
    def test_desugar_expression_if_failure(self):
        a = ['if','a','b',['if',['if'],'d','e']]
        try:
            utils.desugar_expression(a)
        except VentureException as e:
            self.assertEqual(e.data['expression_index'],[3,1])
        else:
            self.fail()

    def test_desugar_expression_and(self):
        a = ['and','a','b']
        b = [['biplex','a',['lambda',[],'b'],['lambda', [], {"type":"boolean","value":False}]]]
        self.assertEqual(utils.desugar_expression(a),b)
    
    def test_desugar_expression_nested(self):
        a = [['and','a','b']]
        b = [[['biplex','a',['lambda',[],'b'],['lambda', [], {"type":"boolean","value":False}]]]]
        self.assertEqual(utils.desugar_expression(a),b)

    def test_desugar_expression_or(self):
        a = ['or','a','b']
        b = [['biplex','a',['lambda', [], {"type":"boolean","value":True}],['lambda',[],'b']]]
        self.assertEqual(utils.desugar_expression(a),b)

    def test_desugar_expression_let_1(self):
        a = ['let',[],'b']
        b = 'b'
        self.assertEqual(utils.desugar_expression(a),b)
    def test_desugar_expression_let_2(self):
        a = ['let',[['a','b']],'c']
        b = [['lambda',['a'],'c'],'b']
        self.assertEqual(utils.desugar_expression(a),b)
    def test_desugar_expression_let_3(self):
        a = ['let',[['a','b'],['c','d']],'e']
        b = [['lambda',['a'],[['lambda',['c'],'e'],'d']],'b']
        self.assertEqual(utils.desugar_expression(a),b)
    def test_desugar_expression_let_failure_1(self):
        a = ['let','a','b']
        try:
            utils.desugar_expression(a)
        except VentureException as e:
            self.assertEqual(e.data['expression_index'],[1])
        else:
            self.fail()
    def test_desugar_expression_let_failure_2(self):
        a = ['let',['a'],'b']
        try:
            utils.desugar_expression(a)
        except VentureException as e:
            self.assertEqual(e.data['expression_index'],[1,0])
        else:
            self.fail()
    def test_desugar_expression_let_failure_3(self):
        a = ['let',[[object(),'c']],'b']
        try:
            utils.desugar_expression(a)
        except VentureException as e:
            self.assertEqual(e.data['expression_index'],[1,0,0])
        else:
            self.fail()

    def test_desugar_expression_identity(self):
        a = ['identity','b']
        b = [['lambda',[],'b']]
        self.assertEqual(utils.desugar_expression(a),b)

    def test_desugar_nothing(self):
        a = ['b']
        b = ['b']
        self.assertEqual(utils.desugar_expression(a),b)


    ######################################
    # desugar_expression
    ######################################

    def find_sym(self, exp, sym):
        if sym==exp:
            return []
        if sym in exp:
            return [exp.index(sym)]
        for i,e in enumerate(exp):
            if isinstance(e,(list,tuple)):
                j = self.find_sym(e,sym)
                if j != None:
                    return [i]+j
        return None

    def test_find_sym(self):
        a = ['if','a','b',['if','c','d','e']]
        self.assertEqual(self.find_sym(a,'a'),[1])
        self.assertEqual(self.find_sym(a,'b'),[2])
        self.assertEqual(self.find_sym(a,'c'),[3,1])
        self.assertEqual(self.find_sym(a,'d'),[3,2])
        self.assertEqual(self.find_sym(a,'e'),[3,3])

    def iter_indices(self,exp):
        yield []
        if isinstance(exp,(list,tuple)):
            for i, e in enumerate(exp):
                for x in self.iter_indices(e):
                    yield [i]+x

    def test_iter_indices(self):
        a = ['a',['b','c'],[]]
        r = [[],[0],[1],[2],[1,0],[1,1]]
        for x in self.iter_indices(a):
            self.assertIn(x,r)
            r.remove(x)
        self.assertEqual(r,[])

    fancy_expressions = [
            ['if','a',['if','b','c','d'],'e'],
            ['and',['and','a','b'],['and','c','d']],
            ['or',['or','a','b'],['or','c','d']],
            [['let',[],[['a'],'b']],['c'],'d'],
            ['let',[['a',['b','c']]],'d'],
            ['let',[['a','b'],['c','d']],'e'],
            ['identity',[['identity',['a','b']],'c','d']]
            ]
    def test_sugar_expression_index_standard_cases(self):
        """make sure that all sugared locations are properly translated"""
        msg_string ="\n\nsym: {}\nsugared_exp: {}\ndesugared_exp: {}\n"\
                    "desugared_index: {}\nexpected_index: {}\n"\
                    "got_index: {}"
        for a in self.fancy_expressions:
            s = utils.desugar_expression(a)
            for sym in ('a','b','c','d'):
                i1 = self.find_sym(a,sym)
                i2 = self.find_sym(s,sym)
                try:
                    i3 = utils.sugar_expression_index(a,i2)
                except:
                    print msg_string.format(sym,a,s,i2,i1,None)
                    raise
                self.assertEqual(i3,i1,msg=msg_string.format(sym,a,s,i2,i1,i3))
    def test_sugar_expression_index_all_cases(self):
        """make sure that none of the edge cases crash the thingy"""
        msg_string ="\n\nsugared_exp: {}\ndesugared_exp: {}\n"\
                    "desugared_index: {}"
        for a in self.fancy_expressions:
            s = utils.desugar_expression(a)
            for i in self.iter_indices(s):
                try:
                    self.assertIsNotNone(utils.sugar_expression_index(a,i),
                            msg=msg_string.format(a,s,i))
                except:
                    print msg_string.format(a,s,i)
                    raise

    def test_desugar_expression_index_standard_cases(self):
        """make sure that all sugared locations are properly translated"""
        msg_string ="\n\nsym: {}\nsugared_exp: {}\ndesugared_exp: {}\n"\
                    "sugared_index: {}\nexpected_index: {}\n"\
                    "got_index: {}"
        for a in self.fancy_expressions:
            s = utils.desugar_expression(a)
            for sym in ('a','b','c','d'):
                i1 = self.find_sym(a,sym)
                i2 = self.find_sym(s,sym)
                try:
                    i3 = utils.desugar_expression_index(a,i1)
                except:
                    print msg_string.format(sym,a,s,i1,i2,None)
                    raise
                self.assertEqual(i3,i2,msg=msg_string.format(sym,a,s,i1,i2,i3))
    def test_desugar_expression_index_all_cases(self):
        """make sure that none of the edge cases crash the thingy"""
        msg_string ="\n\nsugared_exp: {}\ndesugared_exp: {}\n"\
                    "sugared_index: {}"
        for a in self.fancy_expressions:
            s = utils.desugar_expression(a)
            for i in self.iter_indices(a):
                try:
                    self.assertIsNotNone(utils.desugar_expression_index(a,i),
                            msg=msg_string.format(a,s,i))
                except VentureException as e:
                    self.assertEquals(e.exception,'expression_index_desugaring')
                except:
                    print msg_string.format(a,s,i)
                    raise

    def test_validate_instruction_1(self):
        try:
            utils.validate_instruction({},[])
        except VentureException as e:
            self.assertEqual(e.exception,'malformed_instruction')
    def test_validate_instruction_2(self):
        try:
            utils.validate_instruction({'instruction':"moo"},[])
        except VentureException as e:
            self.assertEqual(e.exception,'unrecognized_instruction')
    def test_validate_instruction_3(self):
        i = {'instruction':"moo"}
        self.assertEqual(utils.validate_instruction(i,['moo']),i)

    def test_require_state_1(self):
        utils.require_state('default','red','default')
    def test_require_state_2(self):
        try:
            utils.require_state('moo','default')
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_state')
            self.assertEqual(e.data['state'],'moo')

    def test_validate_symbol_1(self):
        self.assertEqual(utils.validate_symbol('add'),'add')
    def test_validate_symbol_2(self):
        try:
            utils.validate_symbol('9ab')
        except VentureException as e:
            self.assertEqual(e.exception, 'parse')

    def test_validate_value_1(self):
        v = {
            "type":"real",
            "value":1,
            }
        self.assertEqual(utils.validate_value(v),v)
    def test_validate_value_2(self):
        v = {
            "tawfepo":"real",
            "value":1,
            }
        try:
            utils.validate_value(v)
        except VentureException as e:
            self.assertEqual(e.exception, 'parse')

    def test_validate_expression_1(self):
        e = ['a',{'type':'atom','value':1},['b']]
        self.assertEqual(utils.validate_expression(e),e)
    def test_validate_expression_2(self):
        try:
            utils.validate_expression(['a','b',[2]])
        except VentureException as e:
            self.assertEqual(e.exception, 'parse')
            self.assertEqual(e.data['expression_index'], [2,0])

    def test_validate_positive_integer_1(self):
        self.assertEqual(utils.validate_positive_integer(1.0),1)
    def test_sanitize_positive_integer_2(self):
        for i in [-1,0,1.3]:
            try:
                utils.validate_positive_integer(i)
            except VentureException as e:
                self.assertEqual(e.exception, 'parse')

    def test_validate_boolean_1(self):
        self.assertEqual(utils.validate_boolean(True),True)
    def test_validate_boolean_2(self):
        try:
            utils.validate_boolean(1.2)
        except VentureException as e:
            self.assertEqual(e.exception, 'parse')

    def test_validate_arg_1(self):
        i = {"instruction":"moo","symbol":"moo"}
        self.assertEqual(utils.validate_arg(i,"symbol",utils.validate_symbol),"moo")
    def test_validate_arg_2(self):
        i = {"instruction":"moo","symbol":2}
        try:
            utils.validate_arg(i,"symbol",utils.validate_symbol)
        except VentureException as e:
            self.assertEqual(e.exception,'invalid_argument')
            self.assertEqual(e.data['argument'],'symbol')
    def test_validate_arg_3(self):
        i = {"instruction":"moo","symbol":2}
        try:
            utils.validate_arg(i,"red",utils.validate_symbol)
        except VentureException as e:
            self.assertEqual(e.exception,'missing_argument')
            self.assertEqual(e.data['argument'],'red')
    def test_validate_arg_4(self):
        i = {"instruction":"moo"}
        self.assertEqual(utils.validate_arg(i,"red",utils.validate_symbol,required=False),None)
    def test_validate_arg_5(self):
        i = {"instruction":"moo","symbol":"moo"}
        self.assertEqual(utils.validate_arg(i,"symbol",utils.validate_symbol,
            modifier=lambda x: "red"),"red")


