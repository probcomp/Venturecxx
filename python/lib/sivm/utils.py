# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from venture.exception import VentureException
from venture.lite.value import VentureValue
import venture.value.dicts as v

def is_valid_symbol(s):
    if isinstance(s, basestring):
        candidate = s
    elif isinstance(s, dict) and 'type' in s and 'value' in s and s['type'] == 'symbol':
        candidate = s['value']
    else:
        return False
    if not re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', candidate):
        return False
    return True

#############################################
# input sanitization
#############################################

def validate_instruction(instruction,implemented_instructions):
    try:
        instruction_type = instruction['instruction']
    except:
        raise VentureException('malformed_instruction',
                'Sivm instruction is missing the "instruction" key.')
    if instruction_type not in implemented_instructions:
        raise VentureException('unrecognized_instruction',
                'The "{}" instruction is not supported.'.format(instruction_type))
    return instruction

def require_state(cur_state,*args):
    if cur_state not in args:
        raise VentureException('invalid_state',
                'Instruction cannot be executed in the current state, "{}".'.format(cur_state),
                state=cur_state)

def validate_expression(expression):
    if isinstance(expression, basestring):
        validate_symbol(expression)
        return expression
    if isinstance(expression, (list,tuple)):
        for i in range(len(expression)):
            try:
                validate_expression(expression[i])
            except VentureException as e:
                if e.exception == 'parse':
                    e.data['expression_index'].insert(0,i)
                    raise e
                raise
        return expression
    if isinstance(expression, dict):
        validate_value(expression)
        return expression
    if isinstance(expression, VentureValue):
        return expression
    raise VentureException('parse','Expression token must be a string, list, dict, or venture value.',expression_index=[])

def validate_symbol(s):
    if not is_valid_symbol(s):
        raise VentureException('parse',
                'Invalid symbol. May only contain letters, digits, and underscores. May not begin with digit.',
                expression_index=[])
    # TODO Figure out where in the lower levels the symbol-as-string
    # representation is expected and change to dict-symbols.
    if isinstance(s, basestring):
        return s.encode('ascii')
    else:
        return s["value"].encode('ascii')

def validate_dict(s):
    if not isinstance(s,dict):
        raise VentureException('parse',
                'Invalid dictionary.',
                expression_index=[])
    return s

def validate_value(ob):
    try:
        validate_symbol(ob['type']) #validate the type
    except Exception as e:
        raise VentureException('parse',
                'Invalid literal value. {}'.format(e.message),
                expression_index=[])
    return ob

def validate_positive_integer(num):
    if not isinstance(num,(float,int)) or num <= 0 or int(num) != num:
        raise VentureException('parse',
                'Invalid positive integer.',
                expression_index=[])
    return int(num)

def validate_nonnegative_integer(num):
    if not isinstance(num,(float,int)) or num < 0 or int(num) != num:
        raise VentureException('parse',
                'Invalid positive integer.',
                expression_index=[])
    return int(num)

def validate_boolean(b):
    if not isinstance(b,bool):
        raise VentureException('parse',
                'Invalid boolean.',
                expression_index=[])
    return b

def validate_arg(instruction,arg,validator,modifier=lambda x: x,required=True,wrap_exception=True):
    if not arg in instruction:
        if required:
            raise VentureException('missing_argument',
                    'Sivm instruction "{}" is missing '
                    'the "{}" argument'.format(instruction['instruction'],arg),
                    argument=arg)
        return None
    val = instruction[arg]
    try:
        val = validator(val)
    except VentureException as e:
        if e.exception == 'parse' and wrap_exception:
            raise VentureException('invalid_argument',
                    'Invalid argument {}. {}'.format(arg, str(e)),
                    argument=arg)
        raise
    return modifier(val)
