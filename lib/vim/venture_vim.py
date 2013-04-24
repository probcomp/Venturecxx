#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture.exception import VentureException
from venture.vim import utils
import json
import re


class VentureVim(object):

    def __init__(self, core_vim):
        self.core_vim = core_vim
        self.label_dict = {}

    def execute_instruction(self, instruction):
        extra_instructions = ['labeled_assume','labeled_observe',
                'labeled_predict','labeled_forget','labled_report', 'labeled_get_directive_logscore',
                'list_directives','get_directive','labeled_get_directive',
                'force','sample','continuous_inference_config','get_current_exception',
                'get_state', 'list_breakpoints','get_breakpoint']
        # including the ones which may not yet have implementations
        core_instructions = ["assume","observe","predict",
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
