#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture.exception import VentureException
from venture.vim.utils import is_valid_symbol
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
                "clear","rollback","get_global_logscore"]
        try:
            instruction_type = instruction['instruction']
        except:
            raise VentureException('malformed_instruction',
                    'VIM instruction is missing the "instruction" key.')
        if instruction_type not in implemented_instructions:
            raise VentureException('unrecognized_instruction',
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

    def _require_state(self,*args):
        if self.state not in args:
            raise VentureException('invalid_state',
                    'Instruction cannot be executed in the current state, "{}".'.format(self.state),
                    state=self.state)

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
                    '"{}" is not a valid literal value. {}'.format(arg,e.message),
                    argument=arg)

    _symbol_map = { "add" : '+', "sub" : '-',
            "mul" : '*', "div" : "/", "pow" : "power",
            "lt" : "<", "gt" : ">", "lte" : "<=", "gte":
            ">=", "eq" : "=", "neq" : "!=",
            "CRP_make" : "CRP/make",
            "dirichlet_multinomial_make" : "dirichlet-multinomial/make",
            "beta_binomial_make" : "beta-binomial/make",
            "symmetric_dirichlet_multinomial_make" : "symmetric-dirichlet-multinomial/make",
            "symmetric_dirichlet" : "symmetric-dirichlet",
            "noisy_negate" : "noisy-negate",
            "uniform_discrete" : "uniform-discrete",
            "uniform_continuous" : "uniform-continuous",
            "inv_gamma" : "inv-gamma",
            "inv_chisq" : "inv-chisq"}
    def _sanitize_symbol_arg(self,s,arg='symbol'):
        try:
            if not is_valid_symbol(s):
                raise Exception
            if s in self._symbol_map:
                s = self._symbol_map[s]
            return s.encode('ascii')
        except:
            raise VentureException('invalid_argument',
                    '"{}" may only contain letters, digits, and underscores. May not begin with digit.'.format(arg),
                    argument=arg)

    def _sanitize_positive_integer_arg(self,num,arg):
        if not isinstance(num,(float,int)) or num <= 0 or int(num) != num:
            raise VentureException('invalid_argument',
                    '"{}" should be a positive integer.'.format(arg),
                    argument=arg)
        return int(num)

    def _sanitize_boolean_arg(self,b,arg):
        if not isinstance(b,bool):
            raise VentureException('invalid_argument',
                    '"{}" should be a boolean.'.format(arg),
                    argument=arg)
        return b

    _reverse_literal_type_map = dict((y,x) for x,y in _literal_type_map.items())
    def _parse_value(self, val):
        #NOTE: the current c++ implementation ignores the return type -- just gives number
        if isinstance(val,(float,int)):
            return {"type":"number", "value":val}
        else:       #assumed to be string
            t, v = re.match(r'(.*?)\[(.*)\]',val).groups()
            return {"type":self._reverse_literal_type_map[t], "value":json.loads(v)}

    ###############################
    # Error catching
    ###############################

    def _catch_engine_error(vim):
        class tmp(object):
            def __enter__(self):
                pass
            def __exit__(self, type, value, traceback):
                #for now, assume that all un-caught errors are evaluation exceptions
                #with null addresses. in future, also catch breakpoint exceptions and
                #parse exceptions (static value construction is part of parsing)
                if value:
                    vim.state='exception'
                    raise VentureException('evaluation',value.message,address=None)
        return tmp()

    ###############################
    # Instruction implementations
    ###############################

    def _do_assume(self,instruction):
        self._require_args(instruction,'expression','symbol')
        self._require_state('default')
        exp = self._sanitize_expression_arg(instruction['expression'])
        sym = self._sanitize_symbol_arg(instruction['symbol'])
        with self._catch_engine_error():
            did, val = self.engine.assume(sym,exp)
        return {"directive_id":did, "value":self._parse_value(val)}

    def _do_observe(self,instruction):
        self._require_args(instruction,'expression','value')
        self._require_state('default')
        exp = self._sanitize_expression_arg(instruction['expression'])
        val = self._sanitize_value_arg(instruction['value'])
        with self._catch_engine_error():
            try:
                did = self.engine.observe(exp,val)
            except Exception as e:
                m = re.match(r'Rejection sampling has not successfully found any suitable state within (\d+) second\(s\), made iterations: (\d+).',e.message)
                if m:
                    t = int(m.groups()[0])*1000
                    i = int(m.groups()[1])
                    #NOTE: the C++ core is not capable of rolling-back
                    raise VentureException("constraint_timeout", e,
                            runtime=t, iterations=i)
                raise
        return {"directive_id":did}

    def _do_predict(self,instruction):
        self._require_args(instruction,'expression')
        self._require_state('default')
        exp = self._sanitize_expression_arg(instruction['expression'])
        with self._catch_engine_error():
            did, val = self.engine.predict(exp)
        return {"directive_id":did, "value":self._parse_value(val)}

    def _do_configure(self,instruction):
        self._require_state('default')
        s = t = None
        if 'seed' in instruction:
            s = self._sanitize_positive_integer_arg(instruction['seed'],'seed')
        if 'inference_timeout' in instruction:
            t = self._sanitize_positive_integer_arg(instruction['inference_timeout'],'inference_timeout')
        if s != None:
            self.engine.set_seed(s)
        if t != None:
            #do something
            pass
        return {"seed":self.engine.get_seed(), "inference_timeout":5000}

    def _do_forget(self,instruction):
        self._require_args(instruction,'directive_id')
        self._require_state('default')
        did = self._sanitize_positive_integer_arg(instruction['directive_id'],'directive_id')
        try:
            self.engine.forget(did)
        except Exception as e:
            if e.message == 'There is no such directive.':
                raise VentureException('directive_id_not_found',e.message)
            raise
        return {}

    def _do_report(self,instruction):
        self._require_args(instruction,'directive_id')
        self._require_state('default')
        did = self._sanitize_positive_integer_arg(instruction['directive_id'],'directive_id')
        try:
            val = self.engine.report_value(did)
        except Exception as e:
            if e.message == 'Attempt to report value for non-existent directive.':
                raise VentureException('directive_id_not_found',e.message)
            raise
        return {"value":self._parse_value(val)}

    def _do_infer(self,instruction):
        self._require_args(instruction,'iterations','resample')
        self._require_state('default')
        iterations = self._sanitize_positive_integer_arg(instruction['iterations'],'iterations')
        resample = self._sanitize_boolean_arg(instruction['resample'],'resample')
        with self._catch_engine_error():
            #NOTE: model resampling is not implemented in C++
            val = self.engine.infer(iterations)
        return {}

    def _do_clear(self,instruction):
        self._require_state('default')
        self.engine.clear()
        return {}

    def _do_rollback(self,instruction):
        self._require_state('exception','paused')
        #rollback not implemented in C++
        self.state = 'default'
        return {}

    def _do_get_global_logscore(self,instruction):
        self._require_state('default')
        l = self.engine.logscore()
        return {"logscore":l}
