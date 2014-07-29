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

import re

from venture.exception import VentureException
from venture.lite.value import VentureValue
import venture.value.dicts as v

def is_valid_symbol(s):
    if not isinstance(s,basestring):
        return False
    if not re.match(r'[a-zA-Z_][a-zA-Z0-9_]*',s):
        return False
    return True

def desugar_expression(exp):
    """returns a de-sugared version of exp"""
    if isinstance(exp,(list,tuple)) and len(exp) > 0:
        if exp[0] == 'if':
            if len(exp) != 4:
                raise VentureException('parse','"if" statement requires 3 arguments',expression_index=[])
            return [['biplex',dsw(exp,1),['lambda',[],dsw(exp,2)],['lambda',[],dsw(exp,3)]]]
        if exp[0] == 'and':
            if len(exp) != 3:
                raise VentureException('parse','"and" statement requires 2 arguments',expression_index=[])
            return [['biplex',dsw(exp,1),['lambda',[],dsw(exp,2)],['lambda',[],v.boolean(False)]]]
        if exp[0] == 'or':
            if len(exp) != 3:
                raise VentureException('parse','"or" statement requires 2 arguments',expression_index=[])
            return [['biplex',dsw(exp,1),['lambda',[],v.boolean(True)],['lambda',[],dsw(exp,2)]]]
        if exp[0] == 'let':
            if len(exp) != 3:
                raise VentureException('parse','"let" statement requires 2 arguments',expression_index=[])
            if not isinstance(exp[1],(list,tuple)):
                raise VentureException('parse','"let" first argument must be a list',expression_index=[1])
            tmp = dsw(exp,2)
            for index,val in enumerate(exp[1][::-1]):
                if (not isinstance(val, (list,tuple))) or (len(val) != 2):
                    raise VentureException('parse','Invalid (symbol,value) pair "let" statement',expression_index=[1,index])
                if (not isinstance(val[0], basestring)) or (not is_valid_symbol(val[0])):
                    raise VentureException('parse','First argument of pair must be valid symbol',expression_index=[1,index,0])
                tmp = [['lambda', [val[0]], tmp], dsw(val,1)]
            return tmp
        if exp[0] == 'identity':
            if len(exp) != 2:
                raise VentureException('parse','"identity" statement requires 1 argument',expression_index=[])
            return [['lambda',[],dsw(exp,1)]]
        tmp = []
        for i in range(len(exp)):
            tmp.append(dsw(exp,i))
        return tmp
    return exp

def dsw(exp,index):
    """wrapper for a recursive call to desugar_expression"""
    try:
        return desugar_expression(exp[index])
    except VentureException as e:
        if e.exception == 'parse':
            e.data['expression_index'].insert(0,index)
            raise e
        raise

def sugar_expression_index(exp, index):
    """returns a sugared version of index. exp
    should be a sugared expression. index is a
    desugared expression index."""
    if (not isinstance(exp,(tuple,list))) or len(index) == 0:
        return []
    directive = exp[0]
    if directive == 'if':
        if len(index) >= 2:
            if index[1] == 1:
                return [1] + sugar_expression_index(exp[1], index[2:])
        if len(index) >= 3:
            if index[1] == 2 and index[2] == 2:
                return [2] + sugar_expression_index(exp[2], index[3:])
            if index[1] == 3 and index[2] == 2:
                return [3] + sugar_expression_index(exp[3], index[3:])
        return [0]
    if directive == 'and':
        if len(index) >= 2:
            if index[1] == 1:
                return [1] + sugar_expression_index(exp[1], index[2:])
        if len(index) >= 3:
            if index[1] == 2 and index[2] == 2:
                return [2] + sugar_expression_index(exp[2], index[3:])
        return [0]
    if directive == 'or':
        if len(index) >= 2:
            if index[1] == 1:
                return [1] + sugar_expression_index(exp[1], index[2:])
        if len(index) >= 3:
            if index[1] == 3 and index[2] == 2:
                return [2] + sugar_expression_index(exp[2], index[3:])
        return [0]
    if directive == 'let':
        args = len(exp[1])
        tmp_index = index
        for i in range(args):
            if len(tmp_index) >= 1:
                if tmp_index[0] == 1:
                    return [1,i,1] + sugar_expression_index(exp[1][i][1], tmp_index[1:])
            if len(tmp_index) >= 3:
                if tmp_index[1] == 1 and tmp_index[2] == 0:
                    return [1,i,0] + sugar_expression_index(exp[1][i][0], tmp_index[3:])
            if len(tmp_index) < 2:
                return [0]
            tmp_index = tmp_index[2:]
        return [2] + sugar_expression_index(exp[2], tmp_index)
    if directive == 'identity':
        if len(index) >= 2:
            if index[1] == 2:
                return [1] + sugar_expression_index(exp[1], index[2:])
        return [0]
    else:
        return [index[0]] + sugar_expression_index(exp[index[0]], index[1:])


def _raise_eid():
    """raise an expression index desugaring exception"""
    raise VentureException('expression_index_desugaring',
            'Expression index cannot be desugared')

def desugar_expression_index(exp, index):
    """returns a desugared version of index. exp
    should be a syntatically-valid sugared expression.
    index should be a sugared expression index."""
    if (not isinstance(exp,(tuple,list))) or len(index) == 0:
        return []
    directive = exp[0]
    if directive == 'if':
        if index[0] == 0:
            _raise_eid()
        if index[0] == 1:
            return [0,1] + desugar_expression_index(exp[1], index[1:])
        if index[0] == 2:
            return [0,2,2] + desugar_expression_index(exp[2], index[1:])
        if index[0] == 3:
            return [0,3,2] + desugar_expression_index(exp[3], index[1:])
    if directive == 'and':
        if index[0] == 0:
            _raise_eid()
        if index[0] == 1:
            return [0,1] + desugar_expression_index(exp[1], index[1:])
        if index[0] == 2:
            return [0,2,2] + desugar_expression_index(exp[2], index[1:])
    if directive == 'or':
        if index[0] == 0:
            _raise_eid()
        if index[0] == 1:
            return [0,1] + desugar_expression_index(exp[1], index[1:])
        if index[0] == 2:
            return [0,3,2] + desugar_expression_index(exp[2], index[1:])
    if directive == 'let':
        if index[0] == 0:
            _raise_eid()
        if index[0] == 1:
            if len(index) <= 2:
                _raise_eid()
            e = exp[1][index[1]]
            if index[2] == 0:
                return [0,2]*(index[1]) + [0,1,0] + desugar_expression_index(e[0], index[3:])
            if index[2] == 1:
                return [0,2]*(index[1]) + [1] + desugar_expression_index(e[1], index[3:])
        if index[0] == 2:
            return [0,2]*(len(exp[1])) + desugar_expression_index(exp[2], index[1:])
    if directive == 'identity':
        if index[0] == 0:
            _raise_eid()
        if index[0] == 1:
            return [0,2] + desugar_expression_index(exp[1], index[1:])
    return [index[0]] + desugar_expression_index(exp[index[0]], index[1:])


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
    return s.encode('ascii')

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
