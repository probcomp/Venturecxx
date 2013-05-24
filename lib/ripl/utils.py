#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.exception import VentureException

# This list of functions defines the public REST API
# of the Ripl server and client
#
# could have used inspection to generate this list
# of functions, but being explicit is better/more secure
_RIPL_FUNCTIONS = [
        'get_mode','list_available_modes','set_mode',
        'execute_instruction','execute_program','substitute_params',
        'split_program','get_text','character_index_to_expression_index',
        'expression_index_to_text_index','assume','predict',
        'observe','configure','forget','report','infer',
        'clear','rollback','list_directives','get_directive',
        'force','sample','continuous_inference_configure',
        'continuous_inference_enable','continuous_inference_disable',
        'get_current_exception','get_state','get_logscore',
        'get_global_logscore'
        ]