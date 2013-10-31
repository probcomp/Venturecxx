#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re
from venture.parser import utils
import json



class ChurchPrimeParser():
    def __init__(self):

        w = ('+', '-', '*', '/', '<=', '>=', '<', '>', '=', '!=')
        m = {'+':'add', '-':'sub', '*':'mul', '/':'div', '<':'lt',
                '>':'gt', '<=':'lte', '>=':'gte', '=':'eq', '!=':'neq'}

        self.symbol = utils.symbol_token(whitelist_symbols = w, symbol_map = m)

        self.literal = utils.literal_token()

        self.expression = Forward()

        self.combination =  utils.lw(Literal("("))\
                + ZeroOrMore(self.expression)\
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

        # The instruction grammar for churchprime
        # The algorithm for parsing these strings and generating the
        # grammar is located in the utils.py file
        instruction_list = [
            # Directives
            ['assume','[ <!assume> <symbol:sym> <expression:exp> ]'],
            ['labeled_assume','<label:sym> : [ <!assume> <symbol:sym> <expression:exp> ]'],
            ['observe','[ <!observe> <expression:exp> <value:lit> ]'],
            ['labeled_observe','<label:sym> : [ <!observe> <expression:exp> <value:lit> ]'],
            ['predict','[ <!predict> <expression:exp> ]'],
            ['labeled_predict','<label:sym> : [ <!predict> <expression:exp> ]'],
            # Core
            ['configure','[ <!configure> <options:json> ]'],
            ['forget','[ <!forget> <directive_id:int> ]'],
            ['labeled_forget','[ <!forget> <label:sym> ]'],
            ['report','[ <!report> <directive_id:int> ]'],
            ['labeled_report','[ <!report> <label:sym> ]'],
            ['infer','[ <!infer> <iterations:int> <?resample:bool> ]',{"resample":False}],
            ['clear','[ <!clear> ]'],
            ['rollback','[ <!rollback> ]'],
            ['list_directives','[ <!list> <!directives> ]'],
            ['get_directive','[ <!get> <!directive> <directive_id:int> ]'],
            ['labeled_get_directive','[ <!get> <!directive> <label:sym> ]'],
            ['force','[ <!force> <expression:exp> <value:lit> ]'],
            ['sample','[ <!sample> <expression:exp> ]'],
            ['continuous_inference_status','[ <!continuous> <!inference> <!status> ]'],
            ['start_continuous_inference','[ <!start> <!continuous> <!inference> ]'],
            ['stop_continuous_inference','[ <!stop> <!continuous> <!inference> ]'],
            ['get_current_exception', '[ <!get> <!current> <!exception> ]'],
            ['get_state', '[ <!get> <!state> ]'],
            ['get_logscore', '[ <!get> <!logscore> <directive_id:int> ]'],
            ['labeled_get_logscore', '[ <!get> <!logscore> <label:sym> ]'],
            ['get_global_logscore', '[ <!get> <!global> <!logscore> ]'],
            # Profiler
            ['profiler_configure','[ <!profiler> <!configure> <options:json> ]'],
            ['profiler_clear','[ <!profiler> <!configure> ]'],
            ['profiler_list_random_choices', '[ <!profiler> <!list> <!random> <!choices> ]']
        ]

        self.instruction = utils.make_instruction_parser(instruction_list,patterns)
        self.program = utils.make_program_parser(self.instruction)
        self.instruction_strings = utils.make_instruction_strings(instruction_list,antipatterns)

    def get_instruction_string(self,instruction_type):
        return self.instruction_strings[instruction_type]

    def substitute_params(self,instruction_string,args):
        return utils.substitute_params(instruction_string,args)

    def parse_instruction(self, instruction_string):
        return utils.simplify_instruction_parse_tree(
                utils.apply_parser(self.instruction, instruction_string)[0])

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
