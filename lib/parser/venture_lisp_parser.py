#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re
from venture.parser import utils


class VentureLispParser():
    def __init__(self):
        self._reset_stack()

        w = ('+', '-', '*', '/', '<', '>', '<=', '>=', '=', '!=')
        m = {'+':'add', '-':'sub', '*':'mul', '/':'div', '<':'lt',
                '>':'gt', '<=':'lte', '>=':'gte', '=':'eq', '!=':'neq'}

        self.symbol = utils.symbol_token(self.stack, whitelist_symbols = w, symbol_map = m)

        self.value = utils.literal_token(self.stack)

        self.expression = Forward()

        self.combination = ( Literal("(").suppress()
                + OneOrMore(self.expression)
                + Literal(")").suppress())
        def process_combination(s, loc, toks):
            utils.nest_stack(self.stack, loc, len(toks))
            return [list(toks)]
        self.combination.setParseAction(process_combination)

        self.expression << (self.combination | self.value | self.symbol)
        def process_expression(s, loc, toks):
            return list(toks)
        self.expression.setParseAction(process_expression)

        self.instruction, self.program = utils.init_instructions(
                self.value, self.symbol, self.expression, self.stack)

        #disable tab expansion
        self.symbol.parseWithTabs()
        self.value.parseWithTabs()
        self.expression.parseWithTabs()
        self.instruction.parseWithTabs()
        self.program.parseWithTabs()

    def parse_value(self, s):
        return utils.apply_parser(self.value, s)[0]

    def parse_expression(self, s):
        return utils.apply_parser(self.expression, s)[0]

    def parse_symbol(self, s):
        return utils.apply_parser(self.symbol, s)[0]

    def parse_instruction(self, s):
        return utils.apply_parser(self.instruction, s)[0]

    def split_program(self, s):
        self._reset_stack()
        o = utils.apply_parser(self.program, s)[0]
        print self.stack
        output = []
        for i in range(len(o)):
            output.append(utils.get_text_index(self.stack, 0, i))
        return output

    def get_expression_index(self, s, text_index):
        self._reset_stack()
        self.expression.parseString(s)
        return utils._get_parse_tree_index(self.stack,text_index)[1:]

    def get_text_index(self, s, expression_index):
        self._reset_stack()
        self.expression.parseString(s)
        return utils.get_text_index(self.stack, 0, *expression_index)

    def _reset_stack(self):
        self.stack = []

