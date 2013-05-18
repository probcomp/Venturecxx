#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re
from venture.parser import utils

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
    if not toks['value'][0]['value'] == 'identity':
        return toks
    if not isinstance(toks['value'][1]['value'], (list, tuple)):
        return toks
    if toks['value'][1]['value'][0]['value'] == 'identity':
        return {"loc":toks['loc'], "value":[
            toks['value'][0],
            _collapse_identity(toks['value'][1], operators)]}
    if toks['value'][1]['value'][0]['value'] in operators:
        return {"loc":toks['loc'], "value":toks['value'][1]['value']}
    return toks

def _make_infix_token(previous_token, operator_map, lower_precedence, left_to_right = True, swap_order = False):
    """
    generate a token that matches an infix expression and parses it accordingly
    """
    operator_dict = dict(operator_map)
    operator_key_list = list(x[0] for x in operator_map)
    operator_value_list = list(x[1] for x in operator_map)
    def f(s, loc, toks):
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
            operator['value'] = operator_dict[operator['value']]
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

class VentureScriptParser():
    def __init__(self):
        # <expression>
        self.expression = Forward()


        self.reserved_symbols = set(['if','else','proc',
            'true','false','lambda','identity', 'let','add','sub','div',
            'mul','pow','neq','gte','lte', 'eq', 'gt', 'lt', 'and', 'or'])
        self.symbol = utils.symbol_token(blacklist_symbols = self.reserved_symbols)


        self.number = utils.number_token()

        self.string = utils.string_token()

        self.literal = utils.literal_token()


        # <symbol_args>
        #
        # evaluates to a list: [<expression>*]
        def process_symbol_args(s, loc, toks):
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
        def process_expression_args(s, loc, toks):
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
        def process_assignments(s, loc, toks):
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
                        and toks[0]['value'][0]['value'] == 'let':
                    raise ParseException(s, loc,
                        "New scope is not allowed here", self)
                return list(toks)
            l = combine_locs(toks)
            v = [
                    {"loc":l, 'value':'let'},
                    toks[0],
                    toks[1],
                    ]
            return [{"loc":l, "value":v}]
        self.optional_let = self.expression ^ (self.assignments + self.expression)
        self.optional_let.setParseAction(process_optional_let)


        # <identity>
        #
        # evaluates to ["identity", <expression>]
        def process_identity(s, loc, toks):
            l = combine_locs(toks)
            v = [
                    {"loc":l, 'value':'identity'},
                    toks[1],
                    ]
            return [{"loc":l, "value":v}]
        self.identity = lw(Literal("(")) + self.expression + lw(Literal(")"))
        self.identity.setParseAction(process_identity)


        # <if_else>
        #
        # evaluates to ["if", <expression>, <expression>, <expression>]
        def process_if_else(s, loc, toks):
            l = combine_locs(toks)
            v = [
                    {"loc":toks[0]['loc'], 'value':'if'},
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
        def process_proc(s, loc, toks):
            l = combine_locs(toks)
            v = [
                    {"loc":toks[0]['loc'], 'value':'lambda'},
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
        def process_let(s, loc, toks):
            l = combine_locs(toks)
            v = [
                    {"loc":l, 'value':'let'},
                    toks[1],
                    toks[2],
                    ]
            return [{"loc":l, "value":v}]
        self.let = lw(Literal("{")) + self.assignments + self.expression + lw(Literal("}"))
        self.let.setParseAction(process_let)


        # <non_fn_expression>
        #
        # evaluates to itself
        def process_non_fn_expression(s, loc, toks):
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
        def process_fn_application(s, loc, toks):
            if len(toks) == 1:
                return [toks[0]]
            #collapse possible infix identities
            exp = [_collapse_identity(toks[0], ('pow', 'add', 'sub', 'mul', 'div',
                'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or'))]
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
                lower_precedence = ('add', 'sub', 'mul', 'div', 'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or'),
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
                lower_precedence = ('add', 'sub', 'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or'),
                )



        # <add_sub>
        #
        # evaluates to [<op_n-1>, .. [<op_1>, <mul_div_1>, <mul_div_2>] ... , <mul_div_n>]
        # or <mul_div> if no operators provided
        self.add_sub = _make_infix_token(
                previous_token = self.mul_div,    
                operator_map = (('+','add'),('-','sub')),
                lower_precedence = ('eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or'),
                )


        # <comparison>
        #
        # evaluates to [<op_n>, <add_sub_1>, <add_sub_2>, ... , <add_sub_n>]
        # or <add_sub> if no operation token
        self.comparison = _make_infix_token(
                previous_token = self.add_sub,
                operator_map = (('<=','lte'),('>=','gte'),('<','lt'),('>','gt')),
                lower_precedence = ('eq', 'neq', 'and', 'or'),
                )


        # <equality>
        #
        # evaluates to [<op_n>, <comparison_1>, <comparison_2>, ... , <comparison_n>]
        # or <comparison> if no operation token
        self.equality = _make_infix_token(
                previous_token = self.comparison,
                operator_map = (('==','eq'),('!=','neq')),
                lower_precedence = ('and', 'or'),
                )


        # <boolean_and>
        #
        # evaluates to [<op1>, .. [<op2>, <fn_app_n-1>, <fn_app_n>] ... , <fn_app_1>]
        # or <equality> if no exponents provided provided
        self.boolean_and = _make_infix_token(
                previous_token = self.equality,
                operator_map = (('&&','and'),),
                lower_precedence = ('or'),
                )



        # <boolean_or>
        #
        # evaluates to [<op1>, .. [<op2>, <fn_app_n-1>, <fn_app_n>] ... , <fn_app_1>]
        # or <and> if no exponents provided provided
        self.boolean_or = _make_infix_token(
                previous_token = self.boolean_and,
                operator_map = (('||','or'),),
                lower_precedence = (),
                )


        # <expression>
        #
        # evaluates to itself
        def process_expression(s, loc, toks):
            return [toks[0]]
        self.expression << self.boolean_or
        self.expression.setParseAction(process_expression)

        self.instruction, self.program = utils.init_instructions(
                self.literal, self.symbol, self.expression)

        self.program.parseWithTabs()


    # NOTE:
    # the following is copy-pasted from the venture_lisp_parser
    # the two code fragments should be manually kept in sync until 
    # the directive syntax is finalized (then code refactor can happen)

    def value_to_string(self, v):
        return utils.value_to_string(v)

    def parse_value(self, s):
        return utils.apply_parser(self.literal, s)[0]['value']

    def parse_expression(self, s):
        parse_tree = utils.apply_parser(self.expression, s)[0]
        return utils.simplify_expression_parse_tree(parse_tree)

    def parse_symbol(self, s):
        return utils.apply_parser(self.symbol, s)[0]['value']

    def parse_instruction(self, s):
        return utils.simplify_instruction_parse_tree(
                utils.apply_parser(self.instruction, s)[0])

    def parse_program(self, s):
        return utils.simplify_program_parse_tree(
                utils.apply_parser(self.program, s)[0])

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
        locs = {key: list(sorted(loc)) for key,loc in locs.items()}
        return [strings, locs]

    def character_index_to_expression_index(self, s, text_index):
        parse_tree = utils.apply_parser(self.expression, s)[0]
        return utils.get_expression_index(parse_tree, text_index)

    def expression_index_to_text_index(self, s, expression_index):
        parse_tree = utils.apply_parser(self.expression, s)[0]
        return utils.get_text_index(parse_tree, expression_index)
