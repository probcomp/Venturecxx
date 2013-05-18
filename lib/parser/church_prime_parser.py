#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re
from venture.parser import utils


class ChurchPrimeParser():
    def __init__(self):

        w = ('+', '-', '*', '/', '<', '>', '<=', '>=', '=', '!=')
        m = {'+':'add', '-':'sub', '*':'mul', '/':'div', '<':'lt',
                '>':'gt', '<=':'lte', '>=':'gte', '=':'eq', '!=':'neq'}

        self.symbol = utils.symbol_token(whitelist_symbols = w, symbol_map = m)

        self.value = utils.literal_token()

        self.expression = Forward()

        self.combination =  utils.lw(Literal("("))\
                + OneOrMore(self.expression)\
                + utils.lw(Literal(")"))
        def process_combination(s, loc, toks):
            v = toks[1:-1]
            l = utils.combine_locs(toks)
            return [{"loc":l, "value":v}]
        self.combination.setParseAction(process_combination)

        self.expression << (self.combination | self.value | self.symbol)
        def process_expression(s, loc, toks):
            return list(toks)
        self.expression.setParseAction(process_expression)

        self.instruction, self.program = utils.init_instructions(
                self.value, self.symbol, self.expression)

        #disable tab expansion
        self.program.parseWithTabs()

    def value_to_string(self, v):
        return utils.value_to_string(v)

    def parse_value(self, s):
        return utils.apply_parser(self.value, s)[0]['value']

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