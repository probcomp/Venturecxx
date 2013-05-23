#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.ripl import utils
from venture.exception import VentureException


class Ripl():
    def __init__(self,sivm,parsers):
        self.sivm = sivm
        self.parsers = parsers
        self.text_id_to_string = {}
        self.text_id_to_mode = {}
        self.text_id_to_did = {}
        self.did_to_text_id = {}
        self.mode = parsers.keys()[0]
        self._cur_text_id = 0



    ############################################
    # Languages
    ############################################

    def get_mode(self):
        return self.mode

    def list_available_modes(self):
        return self.parsers.keys()

    def set_mode(self, mode):
        if mode in self.parsers:
            self.mode = mode
        else:
            raise VentureException('invalid_mode',
                    "Mode {} is not implemented by this RIPL".format(mode))


    ############################################
    # Execution
    ############################################

    def execute_instruction(self, instruction_string, params=None):
        p = self._cur_parser()
        # perform parameter substitution if necessary
        if params != None:
            instruction_string = self.substitute_params(instruction_string,params)
        # save the text
        self.text_id_to_string[self._next_text_id()] = instruction_string
        self.text_id_to_mode[self._cur_text_id] = self.mode
        # parse instruction
        parsed_instruction = p.parse_instruction(instruction_string)
        # calculate the positions of the arguments
        args, arg_ranges = p.split_instruction(instruction_string)
        try:
            # execute instruction, and handle possible exception
            ret_value = self.sivm.execute_instruction(parsed_instruction)
        except VentureException as e:
            # all exceptions raised by the SIVM get augmented with a
            # a text index (which defaults to the entire instruction)
            e.data['text_index'] = [0,len(instruction_string)-1]
            # in the case of a parse exception, the text_index gets narrowed
            # down to the exact expression/atom that caused the error
            if e.exception == 'parse':
                try:
                    text_index = self._cur_parser().expression_index_to_text_index(
                            args['expression'], e.data['expression_index'])
                    offset = arg_ranges['expression'][0]
                    text_index = [x + offset for x in text_index]
                except VentureException as e2:
                    if e2.exception == 'no_text_index':
                        text_index = None
                    else:
                        raise
                e.data['text_index'] = text_index
            # in case of invalid argument exception, the text index
            # referes to the argument's location in the string
            if e.exception == 'invalid_argument':
                arg = e.data['argument']
                text_index = arg_ranges[arg]
                e.data['text_index'] = text_index
            a = e.data['text_index'][0]
            b = e.data['text_index'][1]+1
            e.data['text_snippet'] = instruction_string[a:b]
            raise
        # if directive, then map the directive id to the text
        if parsed_instruction['instruction'] in ['assume','observe',
                'predict','labeled_assume','labeled_observe','labeled_predict']:
            did = ret_value['directive_id']
            self.did_to_text_id[did] = self._cur_text_id
            self.text_id_to_did[self._cur_text_id] = did
        return (self._cur_text_id, ret_value)


    def execute_program(self, program_string, params=None):
        p = self._cur_parser()
        # perform parameter substitution if necessary
        if params != None:
            program_string = self.substitute_params(program_string,params)
        instructions, positions = p.split_program(program_string)
        vals = []
        for instruction in instructions:
            vals.append(self.execute_instruction(instruction)[1])
        return vals


    ############################################
    # Text manipulation
    ############################################

    def substitute_params(self,instruction_string,params):
        p = self._cur_parser()
        return p.substitute_params(instruction_string,params)

    def split_program(self,program_string):
        p = self._cur_parser()
        return p.split_program(program_string)

    def get_text(self,text_id):
        if text_id in self.text_id_to_mode:
            return [self.text_id_to_mode[text_id], self.text_id_to_string[text_id]]
        return None

    def directive_id_to_text_id(self, directive_id):
        if directive_id in self.did_to_text_id:
            return self.did_to_text_id[directive_id]
        raise VentureException('fatal', 'Directive id {} has no corresponding text id'.format(directive_id))

    def text_id_to_directive_id(self, text_id):
        if text_id in self.text_id_to_did:
            return self.text_id_to_did[text_id]
        raise VentureException('fatal', 'Text id {} has no corresponding directive id'.format(text_id))

    def character_index_to_expression_index(self, text_id, character_index):
        p = self._cur_parser()
        expression, offset = self._extract_expression(text_id)
        return p.character_index_to_expression_index(expression, character_index-offset)

    def expression_index_to_text_index(self, text_id, expression_index):
        p = self._cur_parser()
        expression, offset = self._extract_expression(text_id)
        tmp = p.expression_index_to_text_index(expression, expression_index)
        return [x+offset for x in tmp]


    ############################################
    # Directives
    ############################################

    def assume(self, name, expression, label=None):
        p = self._cur_parser()
        if label==None:
            s = p.get_instruction_string('assume')
            d = {'symbol':name, 'expression':expression}
        else:
            s = p.get_instruction_string('labeled_assume')
            d = {'symbol':name, 'expression':expression, 'label':label}
        return self.execute_instruction(s,d)[1]['value']['value']

    def predict(self, expression, label=None):
        p = self._cur_parser()
        if label==None:
            s = p.get_instruction_string('predict')
            d = {'expression':expression}
        else:
            s = p.get_instruction_string('labeled_predict')
            d = {'expression':expression, 'label':label}
        return self.execute_instruction(s,d)[1]['value']['value']

    def observe(self, expression, value, label=None):
        p = self._cur_parser()
        if label==None:
            s = p.get_instruction_string('observe')
            d = {'expression':expression, 'value':value}
        else:
            s = p.get_instruction_string('labeled_observe')
            d = {'expression':expression, 'value':value, 'label':label}
        self.execute_instruction(s,d)
        return None


    ############################################
    # Core
    ############################################

    def configure(self, options):
        p = self._cur_parser()
        s = p.get_instruction_string('configure')
        d = {'options':options}
        return self.execute_instruction(s,d)[1]['options']


    ############################################
    # Private methods
    ############################################

    def _cur_parser(self):
        return self.parsers[self.mode]

    def _save_did_mapping(self, did, text_range):
        self.did_to_text_id[did] = self._cur_text_id

    def _next_text_id(self):
        self._cur_text_id += 1
        return self._cur_text_id

    def _extract_expression(self,text_id):
        if not text_id in self.text_id_to_did:
            raise VentureException('fatal', 'Text id {} is not a directive'.format(text_id))
        text = self.text_id_to_string[text_id]
        mode = self.text_id_to_mode[text_id]
        p = self.parsers[mode]
        args, arg_ranges = p.split_instruction(text)
        return args['expression'], arg_ranges['expression'][0]
