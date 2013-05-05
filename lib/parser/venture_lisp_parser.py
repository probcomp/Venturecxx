#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re
from venture.parser import utils


class VentureLispParser():
    def __init__(self):

        w = ('+', '-', '*', '/', '<', '>', '<=', '>=', '=', '!=')
        m = {'+':'add', '-':'sub', '*':'mul', '/':'div', '<':'lt',
                '>':'gt', '<=':'lte', '>=':'gte', '=':'eq', '!=':'neq'}

        self.symbol = utils.location_wrapper(
                utils.symbol_token(whitelist_symbols = w, symbol_map = m))

        self.value = utils.location_wrapper(utils.literal_token())

        self.expression = Forward()

        self.combination = ( Literal("(").suppress()
                + OneOrMore(self.expression)
                + Literal(")").suppress())
        def process_combination(s, loc, toks):
            return [list(toks)]
        self.combination.setParseAction(process_combination)
        self.combination = utils.location_wrapper(self.combination)

        self.expression << (self.combination | self.value | self.symbol)
        def process_expression(s, loc, toks):
            return list(toks)
        self.expression.setParseAction(process_expression)

        self.instruction, self.program = utils.init_instructions(
                self.value, self.symbol, self.expression)

        #disable tab expansion
        self.program.parseWithTabs()

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
        strings = utils.get_string_fragments(s, locs)
        return (strings, locs)

    def argument_locations(self, s):
        return utils.split_instruction_parse_tree(
                utils.apply_parser(self.instruction, s)[0])

    def get_expression_index_from_expression(self, s, text_index):
        parse_tree = utils.apply_parser(self.expression, s)[0]
        if not (0 <= text_index < len(s)):
            raise VentureException('no_expression_index', 'Text index is outside the'
                'range of the string')
        return utils.get_expression_index(parse_tree, text_index)

    def get_text_index_from_expression(self, s, expression_index):
        parse_tree = utils.apply_parser(self.expression, s)[0]
        return utils.get_text_index(parse_tree, expression_index)

    def get_expression_index_from_instruction(self, s, text_index):
        parse_tree = utils.apply_parser(self.expression, s)[0]
        if not 'expression' in parse_tree:
            raise VentureException('no_expression_index', 'Instruction must be a directive')
        if not (0 <= text_index < len(s)):
            raise VentureException('no_expression_index', 'Text index is outside the'
                'range of the string')
        return utils.get_expression_index(parse_tree['expression'], text_index)

    def get_text_index_from_instruction(self, s, expression_index):
        parse_tree = utils.apply_parser(self.expression, s)[0]
        if not 'expression' in parse_tree:
            raise VentureException('fatal', 'Instruction must be a directive')
        return utils.get_text_index(parse_tree['expression'], expression_index)
