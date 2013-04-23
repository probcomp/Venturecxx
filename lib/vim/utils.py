#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture.exception import VentureException
import re

def is_valid_symbol(s):
    if re.match(r'[a-zA-Z_][a-zA-Z0-9_]*',s):
        return True
    #TODO: maybe enforce some more reserved words?
    return False

def desugar_expression(exp):
    """returns a de-sugared version of exp"""
    if isinstance(exp,(list,tuple)) and len(exp) > 0:
        if exp[0] == 'if':
            if len(exp) != 4:
                raise VentureException('parse','"if" statement requires 3 arguments',expression_index=[])
            return [['condition_erp',dsw(exp,1),['lambda',[],dsw(exp,2)],['lambda',[],dsw(exp,3)]]]
        if exp[0] == 'and':
            if len(exp) != 3:
                raise VentureException('parse','"and" statement requires 2 arguments',expression_index=[])
            return [['condition_erp',dsw(exp,1),['lambda',[],dsw(exp,2)],{"type":"boolean", "value":False}]]
        if exp[0] == 'or':
            if len(exp) != 3:
                raise VentureException('parse','"or" statement requires 2 arguments',expression_index=[])
            return [['condition_erp',dsw(exp,1),{"type":"boolean", "value":True},['lambda',[],dsw(exp,2)]]]
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
            if len(tmp_index) < 0:
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
