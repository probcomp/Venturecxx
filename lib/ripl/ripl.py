#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture.ripl import utils
from venture.exception import VentureException


class Ripl():
    def __init__(self,vim,parsers):
        self.vim = vim
        self.parsers = parsers
        self.text_id_to_string = {}
        self.did_to_text_id = {}
        self.did_to_mode = {}
        self.did_to_text_range = {}
        self.mode = parsers.keys()[0]
        self._cur_text_id = 0

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

    def execute_instruction(self, instruction, params = None):
        p = self._cur_parser()
        # perform param substitution if necessary
        if params != None:
            instruction = utils.substitute_params(instruction, params, p)
        # save the text
        self.text_id_to_string[self._next_text_id()] = instruction
        # parse and execute the instruction
        parsed_instruction = p.parse_instruction(instruction)
        self.args, self.arg_ranges = p.split_instruction(instruction)
        ret_value = self._exec(parsed_instruction)
        # if directive, then map the directive id to the text
        if parsed_instruction['instruction'] in ['assume','observe',
                'predict','labeled_assume','labeled_observe','labeled_predict']:
            did = ret_value['directive_id']
            self._save_did_mapping(did, self.arg_ranges['expression'])
        return [self._cur_text_id, ret_value]

    def _cur_parser(self):
        return self.parsers[self.mode]

    def _save_did_mapping(self, did, text_range):
        self.did_to_text_id[did] = self._cur_text_id
        self.did_to_mode[did] = self.mode
        self.did_to_text_range[did] = text_range

    def _exec(self, parsed_instruction):
        try:
            return self.vim.execute_instruction(parsed_instruction)
        except VentureException as e:
            e.data['text_index'] = None
            e.data['text_id'] = self._cur_text_id
            if e.exception == 'parse':
                try:
                    text_index = self._cur_parser().expression_index_to_text_index(
                            self.args['expression'], e.data['expression_index'])
                    offset = self.arg_ranges['expression'][0]
                    text_index = [x + offset for x in text_index]
                except VentureException as e2:
                    if e2.exception == 'no_text_index':
                        text_index = None
                    else:
                        raise
                e.data['text_index'] = text_index
            if e.exception == 'invalid_argument':
                arg = e.data['argument']
                text_index = self.arg_ranges[arg]
                e.data['text_index'] = text_index
            raise

    def _next_text_id(self):
        self._cur_text_id += 1
        return self._cur_text_id
