#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from venture.exception import VentureException
from venture.vim import utils
import json
import re
import copy


class CoreVimCppEngine(object):
    ###############################
    # public methods
    ###############################

    def __init__(self):
        from venture.vim import _cpp_engine_extension
        self.engine = _cpp_engine_extension
        self.state = 'default'
        # the current cpp engine doesn't support reporting "observe" directives
        self.observe_dict = {}

    _implemented_instructions = ["assume","observe","predict",
            "configure","forget","report","infer",
            "clear","rollback","get_logscore","get_global_logscore"]
    def execute_instruction(self, instruction):
        utils.validate_instruction(instruction,self._implemented_instructions)
        f = getattr(self,'_do_'+instruction['instruction'])
        return f(instruction)

    ###############################
    # Instruction implementations
    ###############################

    def _do_assume(self,instruction):
        utils.require_state(self.state,'default')
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        sym = utils.validate_arg(instruction,'symbol',
                utils.validate_symbol,modifier=_modify_symbol)
        with self._catch_engine_error():
            did, val = self.engine.assume(sym,exp)
        return {"directive_id":did, "value":_parse_value(val)}

    def _do_observe(self,instruction):
        utils.require_state(self.state,'default')
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        val = utils.validate_arg(instruction,'value',
                utils.validate_value,modifier=_modify_value)
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
        self.observe_dict[did] = instruction
        return {"directive_id":did}

    def _do_predict(self,instruction):
        utils.require_state(self.state,'default')
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        with self._catch_engine_error():
            did, val = self.engine.predict(exp)
        return {"directive_id":did, "value":_parse_value(val)}

    def _do_configure(self,instruction):
        utils.require_state(self.state,'default')
        s = utils.validate_arg(instruction,'seed',
                utils.validate_positive_integer,required=False)
        t = utils.validate_arg(instruction,'inference_timeout',
                utils.validate_positive_integer,required=False)
        if s != None:
            self.engine.set_seed(s)
        if t != None:
            #do something
            pass
        return {"seed":self.engine.get_seed(), "inference_timeout":5000}

    def _do_forget(self,instruction):
        utils.require_state(self.state,'default')
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_positive_integer)
        try:
            self.engine.forget(did)
            if did in self.observe_dict:
                del self.observe_dict[did]
        except Exception as e:
            if e.message == 'There is no such directive.':
                raise VentureException('invalid_argument',e.message,argument='directive_id')
            raise
        return {}

    def _do_report(self,instruction):
        utils.require_state(self.state,'default')
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_positive_integer)
        if did in self.observe_dict:
            return {"value":copy.deepcopy(self.observe_dict[did]['value'])}
        else:
            try:
                val = self.engine.report_value(did)
            except Exception as e:
                if e.message == 'Attempt to report value for non-existent directive.':
                    raise VentureException('invalid_argument',e.message,argument='directive_id')
                raise
            return {"value":_parse_value(val)}

    def _do_infer(self,instruction):
        utils.require_state(self.state,'default')
        iterations = utils.validate_arg(instruction,'iterations',
                utils.validate_positive_integer)
        resample = utils.validate_arg(instruction,'resample',
                utils.validate_boolean)
        with self._catch_engine_error():
            #NOTE: model resampling is not implemented in C++
            val = self.engine.infer(iterations)
        return {}

    def _do_clear(self,instruction):
        utils.require_state(self.state,'default')
        self.engine.clear()
        self.observe_dict = {}
        return {}

    def _do_rollback(self,instruction):
        utils.require_state(self.state,'exception','paused')
        #rollback not implemented in C++
        self.state = 'default'
        return {}

    def _do_get_logscore(self,instruction):
        #TODO: this implementation is a phony
        # it has the same args + state requirements as report,
        # so that code was copy/pasted here just to verify
        # that the directive exists for testing purposes
        utils.require_state(self.state,'default')
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_positive_integer)
        if did not in self.observe_dict:
            try:
                val = self.engine.report_value(did)
            except Exception as e:
                if e.message == 'Attempt to report value for non-existent directive.':
                    raise VentureException('invalid_argument',e.message,argument='directive_id')
                raise
        return {"logscore":0}

    def _do_get_global_logscore(self,instruction):
        utils.require_state(self.state,'default')
        l = self.engine.logscore()
        return {"logscore":l}

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
# Input modification functions
# ----------------------------
# for translating the sanitized
# instructions to and from the
# old C++ instruction format
###############################

def _modify_expression(expression):
    if isinstance(expression, basestring):
        return _modify_symbol(expression)
    if isinstance(expression, (list,tuple)):
        temp = []
        for i in range(len(expression)):
            temp.append(_modify_expression(expression[i]))
        return temp
    if isinstance(expression, dict):
            return _modify_value(expression)

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
def _modify_value(ob):
    if ob['type'] not in _literal_type_map:
        raise VentureException("fatal",
                "Invalid literal type: " + ob["type"])
    t = _literal_type_map[ob['type']]
    v = json.dumps(ob['value'])
    return "{}[{}]".format(t,v).encode('ascii')


_symbol_map = { "add" : '+', "sub" : '-',
        "mul" : '*', "div" : "/", "pow" : "power",
        "lt" : "<", "gt" : ">", "lte" : "<=", "gte":
        ">=", "eq" : "=", "neq" : "!=",
        "crp_make" : "CRP/make",
        "dirichlet_multinomial_make" : "dirichlet-multinomial/make",
        "beta_binomial_make" : "beta-binomial/make",
        "symmetric_dirichlet_multinomial_make" : "symmetric-dirichlet-multinomial/make",
        "symmetric_dirichlet" : "symmetric-dirichlet",
        "noisy_negate" : "noisy-negate",
        "uniform_discrete" : "uniform-discrete",
        "uniform_continuous" : "uniform-continuous",
        "inv_gamma" : "inv-gamma",
        "inv_chisq" : "inv-chisq",
        "condition_erp" : "condition-ERP"}
def _modify_symbol(s):
    if s in _symbol_map:
        s = _symbol_map[s]
    return s.encode('ascii')


_reverse_literal_type_map = dict((y,x) for x,y in _literal_type_map.items())
def _parse_value(val):
    #NOTE: the current c++ implementation ignores the return type -- just gives number
    if isinstance(val,(float,int)):
        return {"type":"number", "value":val}
    else:       #assumed to be string
        # the current implementation just spews garbage
        # t, v = re.match(r'(.*?)\[(.*)\]',val).groups()
        # return {"type":_reverse_literal_type_map[t], "value":json.loads(v)}
        # use this instead
        return {"type":"boolean", "value":True}

