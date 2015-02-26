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
#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyparsing import Literal,Optional,ZeroOrMore,OneOrMore,Forward,\
    ParseException,Keyword,MatchFirst
from venture.parser import utils
import venture.value.dicts as vv
from venture.exception import VentureException

#shortcuts
lw = utils.lw
combine_locs = utils.combine_locs

def _collapse_identity(toks, operators):
    """
    Removes one layer of nested identity functions if the
    inner expression is a function application contained
    in the list of operators. For example:

    _collapse_identity(
        ['identity',
            ['identity',
                ['+', a, b]]],
        ('+'))

    returns: ['identity',
                ['+',a, b]]

    Of course, this function operates on the 'full'
    {"loc":[], "value":[]} representation the above
    parse trees. When a layer of parentheses is
    collapsed, the loc range of the inner expression
    is expanded to include the collapsed parens.
    """
    if not isinstance(toks['value'], (list, tuple)):
        return toks
    if not toks['value'][0]['value'] == vv.sym('identity'):
        return toks
    if not isinstance(toks['value'][1]['value'], (list, tuple)):
        return toks
    if toks['value'][1]['value'][0]['value'] == vv.sym('identity'):
        return {"loc":toks['loc'], "value":[
            toks['value'][0],
            _collapse_identity(toks['value'][1], operators)]}
    if toks['value'][1]['value'][0]['value']['value'] in operators:
        return {"loc":toks['loc'], "value":toks['value'][1]['value']}
    return toks

def _make_infix_token(previous_token, operator_map, lower_precedence, left_to_right = True, swap_order = False):
    """
    generate a token that matches an infix expression and parses it accordingly
    """
    operator_dict = dict(operator_map)
    operator_key_list = list(x[0] for x in operator_map)
    operator_value_list = list(x[1] for x in operator_map)
    def f(_s, _loc, toks):
        """
        generates a function that processes a list of infix tokens into
        the proper binary tree based on certain operator precedence rules
        """
        if len(toks) == 1:
            return [toks[0]]
        #reverse the toks if right-to-left chaining
        if not left_to_right:
            toks = toks[-1::-1]
        #collapse all identities with lower-precedence operators
        for i in range(0, len(toks), 2):
            toks[i] = _collapse_identity(toks[i], lower_precedence)
        #collapse all self-identities at index >= 2
        for i in range(2, len(toks), 2):
            toks[i] = _collapse_identity(toks[i], operator_value_list)
        #construct the parse tree
        exp = toks[0]
        for operator, operand in zip(*(iter(toks[1:]),)*2):
            l = combine_locs([operator, operand, exp])
            operator['value'] = vv.sym(operator_dict[operator['value']])
            if swap_order:
                v = [operator, operand, exp]
            else:
                v = [operator, exp, operand]
            exp = {"loc":l, "value":v}
        return [exp]
    token = previous_token + Optional(\
            ZeroOrMore( lw(MatchFirst((Literal(x) for x in operator_key_list))) + previous_token))
    token.setParseAction(f)
    return token

class VentureScriptParser(object):
    def __init__(self):
        # <expression>
        self.expression = Forward()


        self.reserved_symbols = set(['if','else','proc',
            'true','false','lambda','identity', 'let','add','sub','div',
            'mul','pow','neq','gte','lte', 'eq', 'gt', 'lt', 'and', 'or'])
        self.symbol = utils.symbol_literal_token(blacklist_symbols = self.reserved_symbols)


        self.number = utils.number_token()

        self.string = utils.string_token()

        self.literal = utils.literal_token()


        # <symbol_args>
        #
        # evaluates to a list: [<expression>*]
        def process_symbol_args(_s, _loc, toks):
            v = toks[1:-1:2]
            l = combine_locs(toks)
            return [{"loc":l, "value":v}]
        self.symbol_args = lw(Literal("(")) + (
                    Optional(self.symbol +  ZeroOrMore(lw(Literal(",")) + self.symbol))
                ) + lw(Literal(")"))
        self.symbol_args.setParseAction(process_symbol_args)


        # <expression_args>
        #
        # evaluates to a list: [<expression>*]
        def process_expression_args(_s, _loc, toks):
            v = toks[1:-1:2]
            l = combine_locs(toks)
            return [{"loc":l, "value":v}]
        self.expression_args = lw(Literal("(")) + (
                    Optional(self.expression +  ZeroOrMore(lw(Literal(",")) + self.expression))
                ) + lw(Literal(")"))
        self.expression_args.setParseAction(process_expression_args)


        # <assignments>
        #
        # evaluates to a list of [[<expression>,<expression>]*]
        def process_assignments(_s, _loc, toks):
            symbols = toks[:-2:3]
            expressions = toks[2::3]
            v = [{"loc":combine_locs(x), "value":list(x)} for x in zip(symbols, expressions)]
            l = combine_locs(toks)
            return [{"loc":l, "value":v}]
        self.assignments = OneOrMore(self.symbol + lw(Literal("=")) + self.expression)
        self.assignments.setParseAction(process_assignments)



        # <optional_let>
        #
        # evaluates to a list of ['let', <assignments>, <expression>]
        # or just <expression>
        def process_optional_let(s, loc, toks):
            if len(toks) == 1:
                if isinstance(toks[0]['value'], (list, tuple))\
                        and toks[0]['value'][0]['value'] == vv.sym('let'):
                    raise ParseException(s, loc,
                        "New scope is not allowed here", self)
                return list(toks)
            l = combine_locs(toks)
            v = [
                    {"loc":l, 'value':vv.sym('let')},
                    toks[0],
                    toks[1],
                    ]
            return [{"loc":l, "value":v}]
        self.optional_let = self.expression ^ (self.assignments + self.expression)
        self.optional_let.setParseAction(process_optional_let)


        # <identity>
        #
        # evaluates to ["identity", <expression>]
        def process_identity(_s, _loc, toks):
            l = combine_locs(toks)
            v = [
                    {"loc":l, 'value':vv.sym('identity')},
                    toks[1],
                    ]
            return [{"loc":l, "value":v}]
        self.identity = lw(Literal("(")) + self.expression + lw(Literal(")"))
        self.identity.setParseAction(process_identity)


        # <if_else>
        #
        # evaluates to ["if", <expression>, <expression>, <expression>]
        def process_if_else(_s, _loc, toks):
            l = combine_locs(toks)
            v = [
                    {"loc":toks[0]['loc'], 'value':vv.sym('if')},
                    toks[2],
                    toks[5],
                    toks[9]
                    ]
            return [{"loc":l, "value":v}]
        self.if_else = lw(Keyword("if")) + lw(Literal("(")) +\
                self.optional_let + lw(Literal(")")) + lw(Literal("{")) +\
                self.optional_let + lw(Literal("}")) +\
                lw(Keyword("else")) + lw(Literal("{")) +\
                self.optional_let + lw(Literal("}"))
        self.if_else.setParseAction(process_if_else)


        # <proc>
        #
        # evaluates to ['lambda', <symbol_args>, <expression>]
        def process_proc(_s, _loc, toks):
            l = combine_locs(toks)
            v = [
                    {"loc":toks[0]['loc'], 'value':vv.sym('lambda')},
                    toks[1],
                    toks[3],
                    ]
            return [{"loc":l, "value":v}]
        self.proc = lw(Keyword("proc")) + self.symbol_args +\
                lw(Literal("{")) + self.optional_let +\
                lw(Literal("}") )
        self.proc.setParseAction(process_proc)


        # <let>
        #
        # evaluates to ['let', <assignments>, <expression>]
        def process_let(_s, _loc, toks):
            l = combine_locs(toks)
            v = [
                    {"loc":l, 'value':vv.sym('let')},
                    toks[1],
                    toks[2],
                    ]
            return [{"loc":l, "value":v}]
        self.let = lw(Literal("{")) + self.assignments + self.expression + lw(Literal("}"))
        self.let.setParseAction(process_let)


        # <non_fn_expression>
        #
        # evaluates to itself
        def process_non_fn_expression(_s, _loc, toks):
            return [toks[0]]
        self.non_fn_expression = (
                self.identity |
                self.proc |
                self.if_else |
                self.let |
                self.literal |
                self.symbol
                )


        # <fn_application>
        #
        # evaluates to [ .. [[<non_fn_expression>, *<args1>], *<args2>] .. , *<argsn>]
        # or <non_fn_expression> if no args provided
        def process_fn_application(_s, _loc, toks):
            if len(toks) == 1:
                return [toks[0]]
            #collapse possible infix identities
            exp = [_collapse_identity(toks[0], ('pow', 'add', 'sub', 'mul', 'div',
                                                'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or', '<-'))]
            for args in toks[1:]:
                v = exp+args['value']
                l = combine_locs(exp + [args])
                exp = [{"loc":l, "value":v}]
            return exp
        self.fn_application = self.non_fn_expression + ZeroOrMore(self.expression_args)
        self.fn_application.setParseAction(process_fn_application)


        # <exponent>
        #
        # evaluates to ['power', .. ['power', <fn_app_n-1>, <fn_app_n>] ... , <fn_app_1>]
        # or <fn_application> if no exponents provided provided
        self.exponent = _make_infix_token(
                previous_token = self.fn_application,
                operator_map = (('**','pow'),),
                lower_precedence = ('add', 'sub', 'mul', 'div', 'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or', '<-'),
                left_to_right = False,
                swap_order = True,
                )


        # <mul_div>
        #
        # evaluates to [<op_n-1>, .. [<op_1>, <exponent_1>, <exponent_1>] ... , exponent_n>]
        # or <exponent> if no operators provided
        self.mul_div = _make_infix_token(
                previous_token = self.exponent,
                operator_map = (('*','mul'),('/','div')),
                lower_precedence = ('add', 'sub', 'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or', '<-'),
                )



        # <add_sub>
        #
        # evaluates to [<op_n-1>, .. [<op_1>, <mul_div_1>, <mul_div_2>] ... , <mul_div_n>]
        # or <mul_div> if no operators provided
        self.add_sub = _make_infix_token(
                previous_token = self.mul_div,
                operator_map = (('+','add'),('-','sub')),
                lower_precedence = ('eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or', '<-'),
                )


        # <comparison>
        #
        # evaluates to [<op_n>, <add_sub_1>, <add_sub_2>, ... , <add_sub_n>]
        # or <add_sub> if no operation token
        self.comparison = _make_infix_token(
                previous_token = self.add_sub,
                operator_map = (('<=','lte'),('>=','gte'),('<','lt'),('>','gt')),
                lower_precedence = ('eq', 'neq', 'and', 'or', '<-'),
                )


        # <equality>
        #
        # evaluates to [<op_n>, <comparison_1>, <comparison_2>, ... , <comparison_n>]
        # or <comparison> if no operation token
        self.equality = _make_infix_token(
                previous_token = self.comparison,
                operator_map = (('==','eq'),('!=','neq')),
                lower_precedence = ('and', 'or', '<-'),
                )


        # <boolean_and>
        #
        # evaluates to [<op1>, .. [<op2>, <fn_app_n-1>, <fn_app_n>] ... , <fn_app_1>]
        # or <equality> if no exponents provided provided
        self.boolean_and = _make_infix_token(
                previous_token = self.equality,
                operator_map = (('&&','and'),),
                lower_precedence = ('or', '<-'),
                )



        # <boolean_or>
        #
        # evaluates to [<op1>, .. [<op2>, <fn_app_n-1>, <fn_app_n>] ... , <fn_app_1>]
        # or <and> if no exponents provided provided
        self.boolean_or = _make_infix_token(
                previous_token = self.boolean_and,
                operator_map = (('||','or'),),
                lower_precedence = ('<-'),
                )

        self.do_bind = _make_infix_token(
            previous_token = self.boolean_or,
            operator_map = (('<-','<-'),),
            lower_precedence = (),
        )


        # <expression>
        #
        # evaluates to itself
        def process_expression(_s, _loc, toks):
            return [toks[0]]
        self.expression << self.do_bind # pylint:disable=W0104
        self.expression.setParseAction(process_expression)


        # patterns for converting strings into parsed values
        patterns = {
                "sym":self.symbol,
                "exp":self.expression,
                "lit":self.literal,
                "int":utils.integer_token(),
                "bool":utils.boolean_token(),
                "json":utils.json_value_token(),
                }

        # commands for converting user input into strings
        # which will be parsed in the future according
        # to the 'patterns'. The 's','v','j' refer to the
        # escape sequences used by 'substitute_params'
        antipatterns = {
                "sym":"s",
                "exp":"s",
                "lit":"v",
                "int":"j",
                "bool":"j",
                "json":"j",
                }

        # The instruction grammar for venturescript
        # The algorithm for parsing these strings and generating the
        # grammar is located in the utils.py file
        instruction_list = [
            # Directives
            ['define','<!define> <symbol:sym> = <expression:exp>'],
            ['assume','<!assume> <symbol:sym> = <expression:exp>'],
            ['labeled_assume','<label:sym> : <!assume> <symbol:sym> = <expression:exp>'],
            ['observe','<!observe> <expression:exp> = <value:lit>'],
            ['labeled_observe','<label:sym> : <!observe> <expression:exp> = <value:lit>'],
            ['predict','<!predict> <expression:exp>'],
            ['labeled_predict','<label:sym> : <!predict> <expression:exp>'],
            # Core
            ['forget','<!forget> <directive_id:int>'],
            ['labeled_forget','<!forget> <label:sym>'],
            ['freeze','<!freeze> <directive_id:int>'],
            ['labeled_freeze','<!freeze> <label:sym>'],
            ['report','<!report> <directive_id:int>'],
            ['labeled_report','<!report> <label:sym>'],
            ['infer','<!infer> <expression:exp>'],
            ['clear','<!clear>'],
            ['rollback','<!rollback>'],
            ['list_directives','<!list> <!directives>'],
            ['get_directive','<!get> <!directive> <directive_id:int>'],
            ['labeled_get_directive','<!get> <!directive> <label:sym>'],
            ['force','<!force> <expression:exp> = <value:lit>'],
            ['sample','<!sample> <expression:exp>'],
            ['continuous_inference_status','[ <!continuous> <!inference> <!status> ]'],
            ['start_continuous_inference','[ <!start> <!continuous> <!inference> <expression:exp> ]'],
            ['stop_continuous_inference','[ <!stop> <!continuous> <!inference> ]'],
            ['get_current_exception', '<!get> <!current> <!exception>'],
            ['get_state', '<!get> <!state>'],
            ['get_logscore', '<!get> <!logscore> <directive_id:int>'],
            ['labeled_get_logscore', '<!get> <!logscore> <label:sym>'],
            ['get_global_logscore', '<!get> <!global> <!logscore>'],
            # Ripl
            ['load', '<!load> <file:json>'] # json, a poor man's quoted string
            ]

        self.instruction = utils.make_instruction_parser(instruction_list,patterns)
        self.program = utils.make_program_parser(self.instruction)
        self.instruction_strings = utils.make_instruction_strings(instruction_list,antipatterns)



    # NOTE:
    # the following is copy-pasted from the church_prime_parser
    # the two code fragments should be manually kept in sync until
    # the directive syntax is finalized (then code refactor can happen)

    def get_instruction_string(self,instruction_type):
        return self.instruction_strings[instruction_type]

    def substitute_params(self,instruction_string,args):
        return utils.substitute_params(instruction_string,args)

    def parse_instruction(self, instruction_string):
        return utils.simplify_instruction_parse_tree(
                utils.apply_parser(self.instruction, instruction_string)[0])

    def parse_expression(self, expression_string):
        return utils.simplify_expression_parse_tree(
            utils.apply_parser(self.expression, expression_string)[0])

    def unparse_expression(self, _expression):
        # FIXME: implementation
        raise VentureException("VentureScript can't unparse expressions :(")

    def unparse_instruction(self, instruction):
        def unparse(k, v):
            return self.unparse_expression(v) if k == 'expression' else v
        template = self.instruction_strings[instruction['instruction']]
        param = dict((k, unparse(k, v)) for k, v in instruction.iteritems())
        return self.substitute_params(template, param)

    def parse_number(self, number_string):
        return utils.apply_parser(self.literal, number_string)[0]

    def split_program(self, s):
        locs = utils.split_program_parse_tree(
                utils.apply_parser(self.program, s)[0])
        strings = utils.get_program_string_fragments(s, locs)
        locs = [list(sorted(loc)) for loc in locs]
        return [strings, locs]

    def split_instruction(self, s):
        locs = utils.split_instruction_parse_tree(
                utils.apply_parser(self.instruction, s)[0])
        strings = utils.get_instruction_string_fragments(s, locs)
        locs = dict([(key,list(sorted(loc))) for key,loc in locs.items()])
        return [strings, locs]

    def character_index_to_expression_index(self, expression_string, character_index):
        parse_tree = utils.apply_parser(self.expression, expression_string)[0]
        return utils.get_expression_index(parse_tree, character_index)

    def expression_index_to_text_index(self, expression_string, expression_index):
        parse_tree = utils.apply_parser(self.expression, expression_string)[0]
        return utils.get_text_index(parse_tree, expression_index)

    @staticmethod
    def instance():
        global the_parser # Is a static cache.  How else than globals?  pylint:disable=global-statement
        if the_parser is None:
            the_parser = VentureScriptParser()
        return the_parser

the_parser = None
