#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture.exception import VentureException
import json
import re


class CoreVimCppEngine(object):
    def __init__(self):
        from venture.vim import _cpp_engine_extension
        self.engine = _cpp_engine_extension
        self.state = 'default'

    def execute_instruction(self, instruction):
        implemented_instructions = ["assume","observe","predict",
                "configure","forget","report","infer",
                "clear","rollback","get_logscore",
                "get_global_logscore"]
        try:
            instruction_type = instruction['instruction']
        except:
            raise VentureException('malformed_instruction',
                    'VIM instruction is missing the "instruction" key.')
        if instruction_type not in implemented_instructions:
            raise VentureException('malformed_instruction',
                    'The "{}" instruction is not supported.'.format(instruction_type))
        f = getattr(self,'_do_'+instruction_type)
        return f(instruction)

    ###############################
    # Input sanitization functions
    ###############################

    def _require_args(self,instruction,*args):
        for arg in args:
            if not arg in instruction:
                raise VentureException('missing_argument',
                        'VIM instruction "{}" is missing'
                        'the "{}" argument'.format(instruction['instruction'],arg),
                        argument=arg)

    def _sanitize_expression_arg(self,expression):
        if isinstance(expression, basestring):
            try:
                return self._sanitize_symbol_arg(expression)
            except Exception as e:
                raise VentureException('parse','Invalid symbol. {}'.format(e.message), expression_index=[])
        if isinstance(expression, (list,tuple)):
            temp = []
            for i in range(len(expression)):
                try:
                    temp.append(self._sanitize_expression_arg(expression[i]))
                except VentureException as e:
                    if e.exception == 'parse':
                        e.data['expression_index'].insert(0,i)
                    raise e
            return temp
        if isinstance(expression, dict):
            try:
                return self._sanitize_value_arg(expression)
            except Exception as e:
                raise VentureException('parse','Invalid literal. {}'.format(e.message), expression_index=[])
        raise VentureException('parse','Expression token must be a string, list, or dict.',expression_index=[])

    _literal_type_map = {                     #TODO: data-type support is incomplete in the core
            "smoothed_count" : 'sc',          #so only these types are permitted
            "real" : "r",
            "count" : "c",
            "number" : "r",
            "boolean" : "b",
            "probability" : "p",
            "atom" : "a",
            # simplex point not implemented
            }
    def _sanitize_value_arg(self,ob,arg='value'):
        try:
            t = self._literal_type_map[ob['type']]
            v = json.dumps(ob['value'])
            return "{}[{}]".format(t,v).encode('ascii')
        except Exception as e:
            raise VentureException('invalid_argument',
                    'Invalid literal value. {}'.format(e.message),
                    argument=arg)

    _symbol_map = { "add" : '+', "sub" : '-',
            "mul" : '*', "div" : "/", "pow" : "power",
            "lt" : "<", "gt" : ">", "lte" : "<=", "gte":
            ">=", "eq" : "=", "neq" : "!=" }
    def _sanitize_symbol_arg(self,s,arg='symbol'):
        try:
            if not re.match(r'[a-zA-Z_][a-zA-Z0-9_]*',s):
                raise Exception
            if s in self._symbol_map:
                s = self._symbol_map[s]
            return s.encode('ascii')
        except:
            raise VentureException('invalid_argument',
                    'Symbol may only contain letters, digits, and underscores. May not begin with digit.',
                    argument=arg)

    _reverse_literal_type_map = dict((y,x) for x,y in _literal_type_map.items())
    def _parse_value(self, s):
        t, v = re.match(r'(.*?)\[(.*)\]',s).groups()
        return {"type":self._reverse_literal_type_map[t], "value":json.loads(v)}


    ###############################
    # Instruction implementations
    ###############################

    def _do_assume(self,instruction):
        self._require_args(instruction,'expression','symbol')
        exp = self._sanitize_expression_arg(instruction['expression'])
        sym = self._sanitize_symbol_arg(instruction['symbol'])
        did, val = self.engine.assume(sym,exp)
        #NOTE: the current c++ implementation ignores the return type -- just gives number
        if isinstance(val,(float,int)):
            val = {"type":"number", "value":val}
        else:       #assumed to be string
            val = self._parse_value(val)
        return {"directive_id":did, "value":val}
