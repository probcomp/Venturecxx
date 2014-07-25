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

from pyparsing import Literal,ZeroOrMore,Forward
from venture.parser import utils


class ChurchPrimeParser(object):
    def __init__(self):

        m = {'+':'add', '-':'sub', '*':'mul', '/':'div', '<':'lt',
                '>':'gt', '<=':'lte', '>=':'gte', '=':'eq', '!=':'neq'}
        w = m.keys()

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
            ['infer','[ <!infer> <expression:exp> ]'],
            ['clear','[ <!clear> ]'],
            ['rollback','[ <!rollback> ]'],
            ['list_directives','[ <!list_directives> ]'],
            ['get_directive','[ <!get_directive> <directive_id:int> ]'],
            ['labeled_get_directive','[ <!get_directive> <label:sym> ]'],
            ['force','[ <!force> <expression:exp> <value:lit> ]'],
            ['sample','[ <!sample> <expression:exp> ]'],
            ['continuous_inference_status','[ <!continuous_inference_status> ]'],
            ['start_continuous_inference','[ <!start_continuous_inference> <expression:exp> ]'],
            ['stop_continuous_inference','[ <!stop_continuous_inference> ]'],
            ['get_current_exception', '[ <!get_current_exception> ]'],
            ['get_state', '[ <!get_state> ]'],
            ['get_logscore', '[ <!get_logscore> <directive_id:int> ]'],
            ['labeled_get_logscore', '[ <!get_logscore> <label:sym> ]'],
            ['get_global_logscore', '[ <!get_global_logscore> ]'],
            # Profiler
            ['profiler_configure','[ <!profiler_configure> <options:json> ]'],
            ['profiler_clear','[ <!profiler_configure> ]'],
            ['profiler_list_random_choices', '[ <!profiler_list_random> <!choices> ]']
        ]

        self.instruction = utils.make_instruction_parser(instruction_list,patterns)
        self.program = utils.make_program_parser(self.instruction)
        self.instruction_strings = utils.make_instruction_strings(instruction_list,antipatterns)

    # NOTE:
    # the following is copy-pasted to the venture_script_parser
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

    def unparse_expression(self, expression):
        if isinstance(expression, dict):
            # Should be a leaf value
            return utils.value_to_string(expression)
        elif isinstance(expression, basestring): # Symbol
            return expression
        elif isinstance(expression, list):
            return '(' + ' '.join([self.unparse_expression(e) for e in expression]) + ')'
        else:
            raise Exception("Don't know how to unparse %s" % expression)

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
        global the_parser
        if the_parser is None:
            the_parser = ChurchPrimeParser()
        return the_parser

the_parser = None
