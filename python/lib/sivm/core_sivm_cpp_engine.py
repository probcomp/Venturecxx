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

import json
import re
import copy

from venture.exception import VentureException
from venture.sivm import utils
import venture.value.dicts as v

class CoreSivmCppEngine(object):
    ###############################
    # public methods
    ###############################

    def __init__(self):
        from venture.sivm import _cpp_engine_extension
        self.engine = _cpp_engine_extension
        self.state = 'default'
        # the current cpp engine doesn't support reporting "observe" directives
        self.observe_dict = {}
        # cpp engine doesn't support profiling yet
        self.profiler_enabled = False

    _implemented_instructions = ["assume","observe","predict",
            "configure","forget","report","infer",
            "clear","rollback","get_logscore","get_global_logscore",
            "start_continuous_inference","stop_continuous_inference",
            "continuous_inference_status", "profiler_configure"]
    def execute_instruction(self, instruction):
        utils.validate_instruction(instruction,self._implemented_instructions)
        f = getattr(self,'_do_'+instruction['instruction'])
        return f(instruction)

    ###############################
    # Instruction implementations
    ###############################

    #FIXME: remove the modifier arguments in new implementation
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
                    raise VentureException("constraint_timeout", str(e),
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
        d = utils.validate_arg(instruction,'options',
                utils.validate_dict)
        s = utils.validate_arg(d,'seed',
                utils.validate_positive_integer,required=False)
        t = utils.validate_arg(d,'inference_timeout',
                utils.validate_positive_integer,required=False)
        if s != None:
            self.engine.set_seed(s)
        if t != None:
            #do something
            pass
        return {"options":{"seed":self.engine.get_seed(), "inference_timeout":5000}}

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

    def _do_clear(self,_):
        utils.require_state(self.state,'default')
        self.engine.clear()
        self.observe_dict = {}
        return {}

    def _do_rollback(self,_):
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

    def _do_get_global_logscore(self,_):
        utils.require_state(self.state,'default')
        l = self.engine.logscore()
        return {"logscore":l}
        
    def _do_start_continuous_inference(self,_):
        utils.require_state(self.state,'default')
        with self._catch_engine_error():
            self.engine.start_continuous_inference()
        return {}

    def _do_stop_continuous_inference(self,_):
        utils.require_state(self.state,'default')
        with self._catch_engine_error():
            self.engine.stop_continuous_inference()
        return {}

    def _do_continuous_inference_status(self,_):
        utils.require_state(self.state,'default')
        with self._catch_engine_error():
            return {'running':self.engine.continuous_inference_status()}
    
    ##############################
    # Profiler (stubs)
    ##############################
    
    def _do_profiler_configure(self,instruction):
        utils.require_state(self.state,'default')
        d = utils.validate_arg(instruction, 'options', utils.validate_dict)
        e = utils.validate_arg(d, 'profiler_enabled', utils.validate_boolean, required=False)
        if e != None:
            self.profiler_enabled = e
        return {'options': {'profiler_enabled': self.profiler_enabled}}
    
    ###############################
    # Error catching
    ###############################

    def _catch_engine_error(sivm):
        class tmp(object):
            def __enter__(self):
                pass
            def __exit__(self, type, value, traceback):
                #for now, assume that all un-caught non-venture-exception errors are
                #evaluation exceptions with null addresses. in future, also catch breakpoint
                #exceptions and parse exceptions (static value construction is part of parsing)
                if value:
                    if not type == VentureException:
                        sivm.state='exception'
                        raise VentureException('evaluation',str(value),address=None)
                    raise
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
    # cpp engine does not have robust number parsing
    if int(ob['value']) == ob['value']:
        ob['value'] = int(ob['value'])
    if ob['type'] == 'number':
        if isinstance(ob['value'],int):
            ob['type'] = 'count'
        else:
            ob['type'] = 'real'
    t = _literal_type_map[ob['type']]
    val = json.dumps(ob['value'])
    s = "{0}[{1}]".format(t,val).encode('ascii')
    return s

# the C++ engine now uses the correct symbol names
_symbol_map = { "add" : '+', "sub" : '-',
        "mul" : '*', "div" : "/", "pow" : "power",
        "lt" : "<", "gt" : ">", "lte" : "<=", "gte":
        ">=", "eq" : "=", "neq" : "!=",
        #"crp_make" : "CRP/make",
        #"dirichlet_multinomial_make" : "dirichlet-multinomial/make",
        #"beta_binomial_make" : "beta-binomial/make",
        #"symmetric_dirichlet_multinomial_make" : "symmetric-dirichlet-multinomial/make",
        #"symmetric_dirichlet" : "symmetric-dirichlet",
        #"noisy_negate" : "noisy-negate",
        #"uniform_discrete" : "uniform-discrete",
        #"uniform_continuous" : "uniform-continuous",
        #"inv_gamma" : "inv-gamma",
        #"inv_chisq" : "inv-chisq",
        #"condition_erp" : "condition-ERP"
        }
def _modify_symbol(s):
    if s in _symbol_map:
        s = _symbol_map[s]
    return s.encode('ascii')

_reverse_literal_type_map = dict((y,x) for x,y in _literal_type_map.items())
def _parse_value(val):
    #NOTE: the current c++ implementation ignores the return type -- just gives number
    if isinstance(val, bool):
        return v.boolean(val)
    elif isinstance(val, int):
        return v.integer(val)
    elif isinstance(val, float):
        return v.number(val)
    elif isinstance(val, list):
        return v.list(val)
    elif isinstance(val, tuple):
        return v.simplex(val)
    else:       #assumed to be string
        # try to match one of the known types
        m = re.match(r'(.*?)\[(.*)\]',val)
        if m != None:
            t, val = m.groups()
            return {"type":_reverse_literal_type_map[t], "value":json.loads(val)}
        
        #probably an XRP or compound procedure
        return {"type":"opaque", "value":val}

