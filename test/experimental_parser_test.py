#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture.utils import ExperimentalParser
from pyparsing import ParseException

import time
import sys
import traceback
import StringIO

exponent_ops = [('**','pow')]
add_sub_ops = [('+', 'add'), ('-','sub')]
mul_div_ops = [('*','mul'), ('/','div')]
comparison_ops = [('<=', 'lte'), ('>=', 'gte'), ('<', 'lt'),('>', 'gt')]
equality_ops = [('==','eq'),('!=', 'neq')]
boolean_and_ops = [('&&', 'and')]
boolean_or_ops = [('||','or')]

class Tester():
    def __init__(self, validate=False):
        self.parser = ExperimentalParser()
        self.num_tests = 0
        self.num_failures = 0
        self.failure_list = []
        self.running_time = {}
        self.validate = validate
    def __call__(self, code, expected_result, expression_type):
        expression = getattr(self.parser, expression_type)
        validation_error = None
        if self.validate:
            validation_error = expression.validate()
        result = None
        runtime_error = None
        parse_error = None
        try:
            start_time = time.clock()
            result = list(expression.parseString(code, parseAll=True))
        except ParseException as e:
            parse_error = str(e)
        except Exception as e:
            re_file = StringIO.StringIO()
            traceback.print_exception(*sys.exc_info(), file=re_file)
            runtime_error = re_file.getvalue().replace('\n','\n'+' '*18)
        finally:
            end_time = time.clock()
            self.running_time[self.num_tests] = end_time - start_time
        match = result == expected_result
        print "+++++++++++++++++++++++Test {} {}++++++++++++++++++++++++".format(
                self.num_tests, expression_type)
        print "code:            ", code.replace('\n','\n'+' '*18)
        print "got:             ", result
        print "expected:        ", expected_result
        if validation_error:
            print "validation error:", validation_error
        if runtime_error:
            print "runtime error:   ", runtime_error
        if parse_error:
            print "parse error:     ", parse_error
        print "match:           ", match
        print
        if not match or validation_error or runtime_error:
            self.num_failures += 1
            self.failure_list.append(self.num_tests)
        self.num_tests += 1
        return match
    def print_summary(self):
        print "+++++++++++++++++++++++Summary++++++++++++++++++++++++"
        print "Avg Time: ", sum(self.running_time.values())/len(self.running_time.values())
        print "Slowest:  ", sorted(self.running_time.items(), key=lambda x: -x[1])[:5]
        print "Tests:    ", self.num_tests
        print "Failures: ", self.num_failures
        print "          ", self.failure_list



def run_tests(validate=False):
    tester = Tester(validate=validate)


    # Symbol
    #
    tester( "",
            None,
            "symbol") 
    tester( "3",
            None,
            "symbol") 
    tester( "lambda",
            None,
            "symbol") 
    tester( "if",
            None,
            "symbol") 
    tester( "awef123",
            ["awef123"],
            "symbol") 
    tester( r'awe!@#e',
            None,
            "symbol") 


    # Number
    #
    tester( "",
            None,
            "number") 
    tester( "3",
            [3.0],
            "number") 
    tester( "-3.22",
            [-3.22],
            "number") 
    tester( "3.",
            [3.0],
            "number") 
    tester( "-.3",
            [-.3],
            "number") 
    tester( "moo",
            None,
            "number") 

    
    # Integer
    #
    tester( "",
            None,
            "integer") 
    tester( "3",
            [3],
            "integer") 
    tester( "moo",
            None,
            "integer") 


    # String
    #
    tester( r'',
            None,
            "string") 
    tester( r'"abc"',
            [r'abc'],
            "string") 
    tester( r'"\""',
            [r'"'],
            "string") 
    tester( r'"\n"',
            ['\n'],
            "string") 
    tester( r'"\t"',
            ['\t'],
            "string") 
    tester( r'"\f"',
            ['\f'],
            "string") 
    tester( r'"\062"',
            ['2'],
            "string") 
    tester( r'"\462"',
            None,
            "string") 
    
    # Null
    #
    tester( "",
            None,
            "null") 
    tester( "null",
            [None],
            "null") 


    # Boolean
    #
    tester( "",
            None,
            "boolean") 
    tester( "true",
            [True],
            "boolean") 
    tester( "false",
            [False],
            "boolean") 

    # Json list
    #
    tester( "",
            None,
            "json_list") 
    tester( "[1,2,[3,[]]]",
            [[1,2,[3,[]]]],
            "json_list") 

    # Json object
    #
    tester( "",
            None,
            "json_object") 
    tester( '{"a":{"b":{}}}',
            [{"a":{"b":{}}}],
            "json_object") 

    # Json value
    #
    tester( "",
            None,
            "json_value") 
    tester( r'"abc"',
            [r'abc'],
            "json_value") 
    tester( "null",
            [None],
            "json_value") 
    tester( "true",
            [True],
            "json_value") 
    tester( "[1,2,[3,[]]]",
            [[1,2,[3,[]]]],
            "json_value") 
    tester( '{"a":{"b":{}}}',
            [{"a":{"b":{}}}],
            "json_value") 

    # Value
    #
    tester( "",
            None,
            "value")
    tester( "boolean<true>",
            None,
            "value")
    tester( "number<1.0>",
            None,
            "value")
    tester( "real<1.0>",
            [{"type": "real", "value":1.0}],
            "value")
    tester( 'url<"www.google.com">',
            [{"type": "url", "value":"www.google.com"}],
            "value")
    tester( 'simplex_point<[0.5,0.5]>',
            [{"type": "simplex_point", "value":[0.5,0.5]}],
            "value")
    tester( 'costume<{"hat_color":"blue","shirt_color":"red"}>',
            [{"type": "costume", "value":
                {"hat_color":"blue", "shirt_color":"red"}}],
            "value")


    # Number Literal
    #
    tester( "",
            None,
            "number_literal") 
    tester( "1",
            [{"type":"number", "value":1.0}],
            "number_literal") 


    # Boolean Literal
    #
    tester( "",
            None,
            "boolean_literal") 
    tester( "true",
            [{"type":"boolean", "value":True}],
            "boolean_literal") 


    # Literal
    #
    tester( "",
            None,
            "literal") 
    tester( "1",
            [{"type":"number", "value":1.0}],
            "literal") 
    tester( "true",
            [{"type":"boolean", "value":True}],
            "literal") 
    tester( "real<1.0>",
            [{"type": "real", "value":1.0}],
            "literal")


    # Symbol Args
    #
    tester( "",
            None,
            "symbol_args") 
    tester( "()",
            [[]],
            "symbol_args") 
    tester( "(a)",
            [['a']],
            "symbol_args") 
    tester( "(a, b)",
            [["a",'b']],
            "symbol_args") 


    # Expression Args
    #
    tester( "",
            None,
            "expression_args") 
    tester( "()",
            [[]],
            "expression_args") 
    tester( "(a)",
            [['a']],
            "expression_args") 
    tester( "(a, b)",
            [['a','b']],
            "expression_args") 


    # Optional let expression
    #
    tester( "a",
            ["a"],
            "optional_let") 
    tester( "a=b c",
            [['let', [['a','b']], "c"]],
            "optional_let") 
    tester( "{a=b c}",
            None,
            "optional_let") 


    # Var
    #
    tester( "",
            None,
            "assignments")
    tester( "a=b",
            [[['a','b']]],
            "assignments")
    tester( "a=b c=d",
            [[['a','b'],['c','d']]],
            "assignments")


    # Proc
    #
    tester( "",
            None,
            "proc") 
    tester( "proc(arg, arg){ true }",
            [["lambda", ["arg", "arg"], {'type':'boolean', 'value':True}]],
            "proc") 
    tester( "proc(){ a=b c }",
            [["lambda",[],['let',[["a", 'b']], "c"]]],
            "proc") 


    # Let
    #
    tester( "",
            None,
            "let") 
    tester( "{ a=b c=d e}",
            [["let", [['a','b'], ['c','d']], "e"]],
            "let") 


    # Identity
    #
    tester( "",
            None,
            "identity") 
    tester( "(a)",
            [["identity", 'a']],
            "identity") 


    # If else
    #
    tester( "",
            None,
            "if_else") 
    tester( "if (a) { b }else {c}",
            [["if", "a", "b", "c"]],
            "if_else") 
    tester( "if( a=b c) {d=e f}else{g=h i }",
            [["if",
                ['let',[["a", "b"]], "c"],
                ['let',[["d", "e"]], "f"],
                ['let',[["g", "h"]], "i"],
            ]],
            "if_else") 


    # Function Application
    #
    tester( "",
            None,
            "fn_application") 
    tester( "a(b)(c)",
            [[['a', 'b'], 'c']],
            "fn_application") 
    tester( "a(b, c)",
            [['a', 'b', 'c']],
            "fn_application") 
    tester( "a()",
            [['a']],
            "fn_application") 
    # Function application has precedence over all infix operators
    for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + add_sub_ops + mul_div_ops + exponent_ops: 
        tester( "a" + x + "b()",
                [[y, 'a', ['b']]],
                "expression") 
    # Collapse identities with lesser precedence
    for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + add_sub_ops + mul_div_ops + exponent_ops: 
        tester( "(a" + x + "b)()",
                [[[y, "a", "b"]]],
                "fn_application")
    # Collapse nested identities
    tester( "((a+b))()",
            [[['identity',['add', 'a', 'b']]]],
            "fn_application") 


    # Exponentiation
    #
    tester( "",
            None,
            "exponent") 
    tester( "a**b**c",
            [['pow', 'a', ['pow', 'b', 'c']]],
            "exponent") 
    # Don't collapse redundant identities
    tester( "a**(b**c)",
            [['pow', 'a', ['identity', ['pow', 'b', 'c']]]],
            "exponent") 
    # Collapse non-redundant identities
    tester( "(a**b)**c",
            [['pow', ['pow', 'a', 'b'], 'c']],
            "exponent") 
    tester( "((a**b))**c",
            [['pow', ['identity', ['pow', 'a', 'b']], 'c']],
            "exponent") 
    # Collapse identities with lesser precedence
    for x, y in boolean_and_ops + boolean_or_ops + comparison_ops + equality_ops + add_sub_ops + mul_div_ops: 
        tester( "(a" + x + "b)**c",
                [['pow',[y, "a", "b"], "c"]],
                "exponent") 



    # Multiplication and division
    #
    tester( "",
            None,
            "mul_div") 
    tester( "a*b/c",
            [['div',['mul', 'a', 'b'], 'c']],
            "mul_div") 
    tester( "a/b*c",
            [['mul',['div', 'a', 'b'], 'c']],
            "mul_div") 
    # Don't collapse redundant identities
    tester( "(a*b)/c",
            [['div',['identity', ['mul', 'a', 'b']], 'c']],
            "mul_div") 
    tester( "(a/b)*c",
            [['mul',['identity', ['div', 'a', 'b']], 'c']],
            "mul_div") 
    # Collapse identities with equal precedence
    tester( "a*(b/c)",
            [['mul', 'a', ['div', 'b', 'c']]],
            "mul_div") 
    tester( "a/(b*c)",
            [['div', 'a', ['mul', 'b', 'c']]],
            "mul_div") 
    # Collapse nested identies
    tester( "a/((b/c))",
            [['div', 'a', ['identity', ['div', 'b', 'c']]]],
            "mul_div") 
    tester( "a*(((b*c)))",
            [['mul', 'a', ['identity', ['identity', ['mul', 'b', 'c']]]]],
            "mul_div") 
    # Test that mul_div has medium precedence
    for x, y in exponent_ops:
        tester( "a" + x + "b*c",
                [['mul', [y, "a", "b"], 'c']],
                "mul_div") 
    # Collapse identities with lesser precedence
    for x, y in boolean_and_ops + boolean_or_ops + equality_ops + comparison_ops + add_sub_ops:
        tester( "(a" + x + "b)*c",
                [['mul',[y, "a", "b"], 'c']],
                "mul_div") 
    # Don't collapse identities with greater precedence
    for x, y in exponent_ops:
        tester( "(a" + x + "b)*c",
                [['mul',['identity',[y, "a", "b"]], 'c']],
                "mul_div") 



    # Addition and subtraction
    #
    tester( "",
            None,
            "add_sub") 
    tester( "a+b-c",
            [['sub',['add', 'a', 'b'], 'c']],
            "add_sub") 
    tester( "a-b+c",
            [['add',['sub', 'a', 'b'], 'c']],
            "add_sub") 
    # Don't collapse redundant identities
    tester( "(a+b)-c",
            [['sub',['identity', ['add', 'a', 'b']], 'c']],
            "add_sub") 
    tester( "(a-b)+c",
            [['add',['identity', ['sub', 'a', 'b']], 'c']],
            "add_sub") 
    # Collapse identities with equal precedence
    tester( "a+(b-c)",
            [['add', 'a', ['sub', 'b', 'c']]],
            "add_sub") 
    tester( "a-(b+c)",
            [['sub', 'a', ['add', 'b', 'c']]],
            "add_sub") 
    # Collapse nested identies
    tester( "a-((b-c))",
            [['sub', 'a', ['identity', ['sub', 'b', 'c']]]],
            "add_sub") 
    tester( "a+(((b+c)))",
            [['add', 'a', ['identity', ['identity', ['add', 'b', 'c']]]]],
            "add_sub") 
    # Test that add_sub has medium precedence
    for x, y in exponent_ops + mul_div_ops:
        tester( "a" + x + "b+c",
                [['add', [y, "a", "b"], 'c']],
                "add_sub") 
    # Collapse identities with lesser precedence
    for x, y in boolean_and_ops + boolean_or_ops + equality_ops + comparison_ops:
        tester( "(a" + x + "b)+c",
                [['add',[y, "a", "b"], 'c']],
                "add_sub") 
    # Don't collapse identities with greater precedence
    for x, y in exponent_ops + mul_div_ops:
        tester( "(a" + x + "b)+c",
                [['add',['identity',[y, "a", "b"]], 'c']],
                "add_sub") 

    # Comparison
    #
    tester( "",
            None,
            "comparison") 
    tester( "a<b<c",
            [['lt',['lt', 'a', 'b'],'c']],
            "comparison") 
    # Test all operators
    for x, y in comparison_ops:
        tester( "a" + x + "b",
                [[y, "a", "b"]],
                "comparison") 
    # Test that comparison has low precedence
    for x, y in add_sub_ops + mul_div_ops + exponent_ops:
        tester( "a" + x + "b<c",
                [['lt', [y, "a", "b"], 'c']],
                "comparison") 
    # Collapse identities with lesser precedence
    for x, y in boolean_and_ops + boolean_or_ops + equality_ops:
        tester( "(a" + x + "b)<c",
                [['lt',[y, "a", "b"], 'c']],
                "comparison") 
    # Don't collapse identities with greater precedence
    for x, y in mul_div_ops + exponent_ops + add_sub_ops:
        tester( "(a" + x + "b)<c",
                [['lt',['identity',[y, "a", "b"]], 'c']],
                "comparison") 
    # Collapse identities of equal precedence
    tester( "(a>b)<(c>d)",
            [['lt',['identity',['gt', 'a', 'b']], ['gt', 'c', 'd']]],
            "comparison") 
    # Collapse nested identities
    tester( "a<((b>c))",
            [['lt', 'a', ['identity', ['gt', 'b', 'c']]]],
            "comparison") 

    # Equality
    #
    tester( "",
            None,
            "equality") 
    tester( "a==b==c",
            [['eq',['eq', 'a', 'b'],'c']],
            "equality") 
    # Test all operators
    for x, y in equality_ops:
        tester( "a" + x + "b",
                [[y, "a", "b"]],
                "equality") 
    # Test that equality has low precedence
    for x, y in add_sub_ops + mul_div_ops + exponent_ops + comparison_ops:
        tester( "a" + x + "b==c",
                [['eq', [y, "a", "b"], 'c']],
                "equality") 
    # Collapse identities with lesser precedence
    for x, y in boolean_and_ops + boolean_or_ops:
        tester( "(a" + x + "b)==c",
                [['eq',[y, "a", "b"], 'c']],
                "equality") 
    # Don't collapse identities with greater precedence
    for x, y in mul_div_ops + exponent_ops + add_sub_ops + comparison_ops:
        tester( "(a" + x + "b)==c",
                [['eq',['identity',[y, "a", "b"]], 'c']],
                "equality") 
    # Collapse identities of equal precedence
    tester( "(a!=b)==(c!=d)",
            [['eq',['identity',['neq', 'a', 'b']], ['neq', 'c', 'd']]],
            "equality") 
    # Collapse nested identities
    tester( "a==((b!=c))",
            [['eq', 'a', ['identity', ['neq', 'b', 'c']]]],
            "equality") 


    # And
    #
    tester( "",
            None,
            "boolean_and") 
    tester( "a && b && c",
            [['and', ['and', 'a', 'b'], 'c']],
            "boolean_and") 
    # Don't collapse redundant identities
    tester( "(a&&b)&&c",
            [['and', ['identity', ['and', 'a', 'b']], 'c']],
            "boolean_and") 
    # Collapse non-redundant identities
    tester( "a&&(b&&c)",
            [['and', 'a', ['and', 'b', 'c']]],
            "boolean_and") 
    # Collapse nested identities
    tester( "a&&((b&&c))",
            [['and', 'a', ['identity', ['and', 'b', 'c']]]],
            "boolean_and") 
    # Test that and has low precedence
    for x, y in comparison_ops + equality_ops + add_sub_ops + mul_div_ops + exponent_ops:
        tester( "a" + x + "b&&c",
                [['and', [y, "a", "b"], 'c']],
                "boolean_and") 
    # Collapse identities with lesser precedence
    for x, y in boolean_or_ops:
        tester( "(a" + x + "b)&&c",
                [['and',[y, "a", "b"], 'c']],
                "boolean_and") 
    # Don't collapse identities with greater precedence
    for x, y in comparison_ops + equality_ops + mul_div_ops + exponent_ops + add_sub_ops:
        tester( "(a" + x + "b)&&c",
                [['and',['identity',[y, "a", "b"]], 'c']],
                "boolean_and") 

    # Or
    #
    tester( "",
            None,
            "boolean_or") 
    tester( "a || b || c",
            [['or', ['or', 'a', 'b'], 'c']],
            "boolean_or") 
    # Don't collapse redundant identities
    tester( "(a||b)||c",
            [['or', ['identity', ['or', 'a', 'b']], 'c']],
            "boolean_or") 
    # Collapse non-redundant identities
    tester( "a||(b||c)",
            [['or', 'a', ['or', 'b', 'c']]],
            "boolean_or") 
    # Collapse nested identities
    tester( "a||((b||c))",
            [['or', 'a', ['identity', ['or', 'b', 'c']]]],
            "boolean_or") 
    # Test that or has low precedence
    for x, y in comparison_ops + equality_ops + add_sub_ops + mul_div_ops + exponent_ops:
        tester( "a" + x + "b||c",
                [['or', [y, "a", "b"], 'c']],
                "boolean_or") 
    # Don't collapse identities with greater precedence
    for x, y in comparison_ops + equality_ops + mul_div_ops + exponent_ops + add_sub_ops:
        tester( "(a" + x + "b)||c",
                [['or',['identity',[y, "a", "b"]], 'c']],
                "boolean_or") 


    # Expression
    #
    tester( "",
            None,
            "expression") 
    #identity
    tester( "(a)",
            [["identity", 'a']],
            "expression") 
    #let
    tester( "{ a=b c=d e}",
            [["let", [['a','b'], ['c','d']], "e"]],
            "expression") 
    #proc
    tester( "proc(){ a=2 b }",
            [["lambda",[],['let',[["a", {'type':'number', 'value':2.0}]], "b"]]],
            "expression") 
    #symbol
    tester( "b",
            ['b'],
            "expression") 
    #literal
    tester( "3",
            [{'type':'number', 'value':3.0}],
            "expression") 
    #if_else
    tester( "if (a) { b }else {c}",
            [["if", "a", "b", "c"]],
            "expression") 
    #function application
    tester( "a(b)(c)",
            [[['a', 'b'], 'c']],
            "expression") 
    #exponentiation
    tester( "a**b**c",
            [['pow', 'a', ['pow', 'b', 'c']]],
            "expression") 
    #mul_div
    tester( "a*b/c",
            [['div',['mul', 'a', 'b'], 'c']],
            "expression") 
    #add_sub
    tester( "a+b-c",
            [['sub',['add', 'a', 'b'], 'c']],
            "expression") 
    #comparision
    tester( "a==b==c",
            [['eq', ['eq', 'a', 'b'], 'c']],
            "expression") 
    #boolean
    tester( "true && true || true",
            [['or', ['and', {'type':'boolean', 'value':True}, {'type':'boolean', 'value':True}], {'type':'boolean', 'value':True}]],
            "expression") 


    # Assume
    #
    tester( "",
            None,
            "assume")
    tester( "assuMe blah = moo",
            [{
                "instruction" : "assume",
                "symbol" : "blah",
                "expression" : "moo"
                }],
            "assume")


    # Predict
    #
    tester( "",
            None,
            "predict")
    tester( "prediCt blah",
            [{
                "instruction" : "predict",
                "expression" : "blah",
                }],
            "predict")


    # Observe
    #
    tester( "",
            None,
            "observe")
    tester( "obServe blah = 1.3",
            [{
                "instruction" : "observe",
                "expression" : "blah",
                "value" : {"type":"number", "value":1.3},
                }],
            "observe")


    # Forget
    #
    tester( "",
            None,
            "forget")
    tester( "forget blah",
            [{
                "instruction" : "forget",
                "label" : "blah",
                }],
            "forget")
    tester( "FORGET 34",
            [{
                "instruction" : "forget",
                "directive_id" : 34,
                }],
            "forget")


    # Sample
    #
    tester( "",
            None,
            "sample")
    tester( "saMple blah",
            [{
                "instruction" : "sample",
                "expression" : "blah",
                }],
            "sample")


    # Force
    #
    tester( "",
            None,
            "force")
    tester( "force blah = count<132>",
            [{
                "instruction" : "force",
                "expression" : "blah",
                "value" : {'type':'count', 'value':132.0},
                }],
            "force")


    # Infer
    #
    tester( "",
            None,
            "infer")
    tester( "infer 132",
            [{
                "instruction" : "infer",
                "iterations" : 132,
                "resample" : False,
                }],
            "infer")


    # Named directive
    #
    tester( "",
            None,
            "named_directive")
    tester( "name : assume a = b",
            [{
                "instruction" : "assume",
                "symbol" : "a",
                "expression" : "b",
                "label" : 'name',
                }],
            "named_directive")
    tester( "name : predict blah",
            [{
                "instruction" : "predict",
                "expression" : "blah",
                "label" : 'name',
                }],
            "named_directive")
    tester( "name : observe a = count<32>",
            [{
                "instruction" : "observe",
                "expression" : "a",
                "value" : {'type':'count', 'value':32.0},
                "label" : 'name',
                }],
            "named_directive")

    #Skip test for unnamed_directive and directive

    # Program
    #
    tester( "",
            [],
            "program")
    tester( """
    name: assume a = b
    observe a = 23
    predict
        if (flip()){
            a = 4
            a
        } else {
            b
        }
    infer 244
    """,
            [
                {
                    "instruction" : "assume",
                    "symbol" : "a",
                    "expression" : "b",
                    "label" : "name",
                    },
                {
                    "instruction" : "observe",
                    "expression" : "a",
                    "value" : {'type':'number', 'value':23.0},
                    },
                {
                    "instruction" : "predict",
                    "expression" : ["if", ["flip"], ['let', [['a',{'type':'number', 'value':4.0}]], "a"], "b"]
                    },
                {
                    "instruction" : "infer",
                    "iterations" : 244,
                    "resample" : False,
                    }
                ],
            "program")
    tester( """
    predict (1 + 4)/3**5.11 + 32*4-2
    """,
            [
                {
                    "instruction" : "predict",
                    "expression" : ['sub',
                        ['add',
                            ['div',['add',{'type':'number','value':1.0},{'type':'number','value':4.0}],['pow',{'type':'number','value':3.0},{'type':'number','value':5.11}]],
                            ['mul',{'type':'number','value':32.0},{'type':'number','value':4.0}],
                            ],
                        {'type':'number','value':2.0}],
                    },
                ],
            "program")
    
    # Advanced curve fitting demo
    tester( """
    ASSUME model_type = uniform_discrete(0,2)
    ASSUME outlier_prob = uniform_continuous( 0.001, 0.3)
    ASSUME outlier_sigma = uniform_continuous( 0.001, 100.0)
    ASSUME noise = uniform_continuous(0.1, 1.0)
    ASSUME alpha =
        if (model_type == 0){
            1
        }else {
            if( model_type == 1) {
                0
            } else {
                beta(1,1)
            }
        }
    ASSUME poly_order = uniform_discrete(0,4)
    ASSUME a0_c0 = normal(0.0, 10.0)
    ASSUME c1 =
        proc(value){
            if (poly_order >= 1 ){
                value
            } else {
                0.0
            }
        }(normal(0.0, 1.0))
    ASSUME c2 =
        proc(value){
            if (poly_order >= 2){
                value
            } else {
                0.0
            }
        }(normal(0.0, 0.1))
    ASSUME c3 =
        proc(value){
            if (poly_order >= 3){
                value
            } else {
                0.0
            }
        }(normal(0.0, 0.01))
    ASSUME c4 =
        proc(value){
            if (poly_order >= 4){
                value
            } else {
                0.0
            }
        }(normal(0.0, 0.001))
    ASSUME fourier_a1 = normal(0.0, 5.0)
    ASSUME fourier_omega = uniform_continuous(3.14/50, 3.14*1)
    ASSUME fourier_theta1 = uniform_continuous(-3.14, 3.14)
    ASSUME clean_func_poly=
        proc (x){
            c1*x**1.0 + c2*x**2.0 + c3*x**3.0 + c4*x**4.0
        }
    ASSUME clean_func_fourier =
        proc(x){
            fourier_a1 * sin(fourier_omega*x*1 + fourier_theta1)
        }
    ASSUME clean_func =
        proc(x){
            a0_c0 + alpha*clean_func_poly(x) + (1-alpha)*clean_func_fourier(x)
        }
    PREDICT list(poly_order, a0_c0, c1, c2, c3, c4, noise, alpha,
        fourier_a1, fourier_omega, fourier_theta1)
            
""",
    [   {"instruction" : 'assume', 'symbol': 'model_type', 'expression': ['uniform_discrete', {'type':'number','value':0.0}, {'type':'number','value':2.0}]},
            {"instruction" : "assume", "symbol" : 'outlier_prob', "expression": ['uniform_continuous', {'type':'number','value':0.001}, {'type':'number','value':0.3}]},
            {"instruction" : "assume", "symbol": 'outlier_sigma', "expression": ['uniform_continuous', {'type':'number','value':0.001}, {'type':'number','value':100.0}]},
            {"instruction": 'assume', 'symbol': 'noise', 'expression': ['uniform_continuous', {'type':'number','value':0.1}, {'type':'number','value':1.0}]},
    {"instruction":"assume",
        "symbol":'alpha',
        "expression" : [   'if',
            ['eq', 'model_type', {'type':'number','value':0.0}],
            {'type':'number','value':1.0},
            ['if', ['eq', 'model_type', {'type':'number','value':1.0}], {'type':'number','value':0.0}, ['beta', {'type':'number','value':1.0}, {'type':'number','value':1.0}]]]},
        {"instruction" : "assume", "symbol": 'poly_order', "expression": ['uniform_discrete', {'type':'number','value':0.0}, {'type':'number','value':4.0}]},
        {"instruction":"assume", "symbol": 'a0_c0',"expression": ['normal', {'type':'number','value':0.0}, {'type':'number','value':10.0}]},
        {"instruction":"assume",
            "symbol":'c1',
            "expression":[   [   'lambda',
                ['value'],
                ['if', ['gte', 'poly_order', {'type':'number','value':1.0}], 'value', {'type':'number','value':0.0}]],
                ['normal', {'type':'number','value':0.0}, {'type':'number','value':1.0}]]},
            {"instruction":"assume",
                'symbol':'c2',
                "expression":[   [   'lambda',
                ['value'],
                ['if', ['gte', 'poly_order', {'type':'number','value':2.0}], 'value', {'type':'number','value':0.0}]],
                ['normal', {'type':'number','value':0.0}, {'type':'number','value':0.1}]]},
                {"instruction":"assume",
                    "symbol":'c3',
                    'expression':[   [   'lambda',
                ['value'],
                ['if', ['gte', 'poly_order', {'type':'number','value':3.0}], 'value', {'type':'number','value':0.0}]],
                ['normal', {'type':'number','value':0.0}, {'type':'number','value':0.01}]]},
                    {'instruction':'assume',
                        'symbol':'c4',
                        'expression':[   [   'lambda',
                ['value'],
                ['if', ['gte', 'poly_order', {'type':'number','value':4.0}], 'value', {'type':'number','value':0.0}]],
                ['normal', {'type':'number','value':0.0}, {'type':'number','value':0.001}]]},
                        {"instruction":'assume', 'symbol':'fourier_a1', 'expression':['normal', {'type':'number','value':0.0}, {'type':'number','value':5.0}]},
                        {"instruction":"assume",
                            'symbol':'fourier_omega',
                            'expression':['uniform_continuous', ['div', {'type':'number','value':3.14}, {'type':'number','value':50.0}], ['mul', {'type':'number','value':3.14}, {'type':'number','value':1.0}]]},
                        {'instruction':"assume", "symbol":'fourier_theta1', 'expression':['uniform_continuous', {'type':'number','value':-3.14}, {'type':'number','value':3.14}]},
                        {"instruction":"assume",
                            "symbol":'clean_func_poly',
                            "expression":[   'lambda',
            ['x'],
            [   'add', ['add', ['add',
                ['mul', 'c1', ['pow', 'x', {'type':'number','value':1.0}]],
                ['mul', 'c2', ['pow', 'x', {'type':'number','value':2.0}]]],
                ['mul', 'c3', ['pow', 'x', {'type':'number','value':3.0}]]],
                ['mul', 'c4', ['pow', 'x', {'type':'number','value':4.0}]]]]},
            {"instruction":"assume",
                    "symbol":'clean_func_fourier',
                    'expression':[   'lambda',
            ['x'],
            [   'mul',
                'fourier_a1',
                [   'sin',
                    [   'add',
                        ['mul', ['mul', 'fourier_omega', 'x'], {'type':'number','value':1.0}],
                        'fourier_theta1']]]]},
                    {"instruction":'assume',
                            'symbol':'clean_func',
                            'expression':[   'lambda',
            ['x'],
            [   'add', ['add',
                'a0_c0',
                ['mul', 'alpha', ['clean_func_poly', 'x']]],
                ['mul', ['sub', {'type':'number','value':1.0}, 'alpha'], ['clean_func_fourier', 'x']]]]},
            {
                    "instruction":"predict",
                    "expression":[   'list',
            'poly_order',
            'a0_c0',
            'c1',
            'c2',
            'c3',
            'c4',
            'noise',
            'alpha',
            'fourier_a1',
            'fourier_omega',
            'fourier_theta1']}],
        "program")


    tester.print_summary()
    return tester.num_failures == 0




if __name__ == "__main__":
    validate = '--validate' in sys.argv
    if run_tests(validate):
        exit(0)
    exit(1)
