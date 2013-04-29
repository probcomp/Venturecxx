#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re
from venture.parser import utils


class VentureLispParser():
    def __init__(self):
        self.expression = Forward()

        self.symbol = utils.symbol_token()

        self.value = utils.literal_token()

        self.expression << ( Literal("(").suppress()
                + OneOrMore(self.symbol | self.value | self.expression)
                + Literal(")").suppress())
        def process_expression(s, loc, toks):
            return list(toks)
        self.expression.setParseAction(process_expression)

    def parse_value(self, s):
        pass

    def parse_expression(self, s):
        pass

    def parse_symbol(self, s):
        pass

    def parse_instruction(self, s):
        pass

    def split_program(self, s):
        pass

    def get_expression_index(self, s, text_index):
        pass

    def get_text_index(self, s, expression_index):
        pass
