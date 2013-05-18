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

        self.literal = utils.literal_token()

        self.expression = Forward()

        self.combination =  utils.lw(Literal("("))\
                + OneOrMore(self.expression)\
                + utils.lw(Literal(")"))
        def process_combination(s, loc, toks):
            v = toks[1:-1]
            l = utils.combine_locs(toks)
            return [{"loc":l, "value":v}]
        self.combination.setParseAction(process_combination)

        self.expression << (self.combination | self.literal | self.symbol)
        def process_expression(s, loc, toks):
            return list(toks)
        self.expression.setParseAction(process_expression)

        # Instruction syntax
        patterns = {
                "sym":self.symbol,
                "exp":self.expression,
                "lit":self.literal,
                "int":utils.integer_token(),
                "bool":utils.boolean_token(),
                }

        instruction_list = [
            ['assume','<!assume> <symbol:sym> = <expression:exp>'],
            ['labeled_assume','<label:sym> : <!assume> <symbol:sym> = <expression:exp>'],
            ['observe','<!observe> <expression:exp> = <value:lit>'],
            ['labeled_observe','<label:sym> : <!observe> <expression:exp> = <value:lit>'],
            ['predict','<!predict> <expression:exp>'],
            ['labeled_predict','<label:sym> : <!predict> <expression:exp>'],
            ['forget','<!forget> <directive_id:int>'],
            ['labeled_forget','<!forget> <label:sym>'],
            ['force','<!force> <expression:exp> = <value:lit>'],
            ['sample','<!sample> <expression:exp>'],
            ['infer','<!infer> <iterations:int> <?resample:bool>',{"resample":False}],
            ['clear','<!clear>'],
            ]

        self.instruction = utils.make_instruction_parser(instruction_list,patterns)
        self.program = utils.make_program_parser(self.instruction)

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
