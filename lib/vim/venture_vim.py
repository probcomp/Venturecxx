#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture.exception import VentureException
from venture.vim import utils
import json
import re


class VentureVim(object):

    def __init__(self, core_vim):
        self.core_vim = core_vim
        self._clear()

    # list of all instructions supported by venture vim
    _extra_instructions = ['labeled_assume','labeled_observe',
            'labeled_predict','labeled_forget','labled_report', 'labeled_get_directive_logscore',
            'list_directives','get_directive','labeled_get_directive',
            'force','sample','continuous_inference_config','get_current_exception',
            'get_state', 'list_breakpoints','get_breakpoint']
    _core_instructions = ["assume","observe","predict",
            "configure","forget","report","infer",
            "clear","rollback","get_directive_logscore","get_global_logscore",
            "debugger_configure","debugger_list_random_choices", "debugger_clear",
            "debugger_force_random_choice","debugger_report_address",
            "debugger_history","debugger_dependents","debugger_address_to_source_code_location",
            "debugger_set_breakpoint_address","debugger_set_breakpoint_source_code_location",
            "debugger_remove_breakpoint","debugger_continue","profiler_configure",
            "profiler_clear","profiler_list_random_choices",
            "profiler_address_to_source_code_location","profiler_get_random_choice_acceptance_rate",
            "profiler_get_global_acceptance_rate","profiler_get_random_choice_proposal_time",
            "profiler_get_global_proposal_time"]
    def execute_instruction(self, instruction):
        utils.validate_instruction(instruction,self._core_instructions + self._extra_instructions)
        instruction_type = instruction['instruction']
        with self._pause_continuous_inference():
            if instruction_type in self._extra_instructions:
                f = getattr(self,'_do_'+instruction_type)
                return f(instruction)
            return self._call_core_vim_instruction(instruction)

    ###############################
    # Reset stuffs
    ###############################

    def _clear(self):
        self.label_dict = {}
        self.directive_dict = {}
        self._debugger_clear()
        self.state = 'default'

    def _debugger_clear(self):
        self.breakpoint_dict = {}

    ###############################
    # Sugars/desugars
    # for the CoreVim instructions
    ###############################

    def _call_core_vim_instruction(self,instruction):
        desugared_instruction = instruction.copy()
        instruction_type = instruction['instruction']
        # desugar the expression
        if instruction_type in ['assume','observe','predict']:
            exp = utils.validate_arg(instruction,'expression',
                    utils.validate_expression, wrap_exception=False)
            new_exp = utils.desugar_expression(exp)
            desugared_instruction['expression'] = new_exp
        # desugar the expression index
        if instruction_type == 'debugger_set_breakpoint_source_code_location':
            desugared_src_location = desugared_instruction['source_code_location']
            did = desugared_src_location['directive_id']
            old_index = desugared_src_location['expression_index']
            exp = self.directive_dict[did]['expression']
            new_index = utils.desugar_expression_index(exp, old_index)
            desugared_src_location['expression_index'] = new_index
        try:
            response = self.core_vim.execute_instruction(desugared_instruction)
        except VentureException as e:
            if e.exception == "evaluation":
                self.state='exception'
            if e.exception == "breakpoint":
                self.state='paused'
            # re-sugar the expression index
            if e.exception == 'parse':
                i = e.data['expression_index']
                exp = instruction['expression']
                i = utils.sugar_expression_index(exp,i)
                e.data['expression_index'] = i
            raise
        # clear the dicts on the "clear" command
        if instruction_type == 'clear':
            self._clear()
        # save the directive
        if instruction_type in ['assume','observe','predict']:
            did = response['directive_id']
            self.directive_dict[did] = instruction
        if instruction_type in ['debugger_set_breakpoint_address',
                'debugger_set_breakpoint_source_code_location']:
            bid = response['breakpoint_id']
            #NOTE: the extra "instruction" key shouldn't be a problem
            self.breakpoint_dict[bid] = instruction 
        return response


    ###############################
    # Continuous Inference Pauser
    ###############################

    def _pause_continuous_inference(vim):
        class tmp(object):
            def __enter__(self):
                pass
            def __exit__(self, type, value, traceback):
                pass
        return tmp()


    ###############################
    # Continuous Inference Pauser
    ###############################
    def _do_labeled_assume(self, instruction):
        self.label_dict[label] = did
