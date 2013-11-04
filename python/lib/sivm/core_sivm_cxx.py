#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.exception import VentureException
from venture.sivm import utils
import json
import re
import copy
import thread, threading

class CoreSivmCxx(object):
    ###############################
    # public methods
    ###############################

    def __init__(self):
	# TODO: merge venture.cxx.sivm into this file
        from venture.cxx import sivm
        self.engine = sivm.SIVM()
        self.state = 'default'
        # the current cpp engine doesn't support reporting "observe" directives
        self.observe_dict = {}
        # cpp engine doesn't support profiling yet
        self.profiler_enabled = False
        
        self.continuous_inference_running = False
        self.continuous_inference_lock = threading.Lock()

    _implemented_instructions = ["assume","observe","predict",
            "configure","forget","report","infer",
            "clear","rollback","get_logscore","get_global_logscore",
            "start_continuous_inference","stop_continuous_inference",
            "continuous_inference_status", "profiler_configure"]
    def execute_instruction(self, instruction):
        utils.validate_instruction(instruction,self._implemented_instructions)
        f = getattr(self,'_do_'+instruction['instruction'])
        with self.continuous_inference_lock:
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
        did, val = self.engine.assume(sym,exp)
        return {"directive_id":did, "value":_parse_value(val)}

    def _do_observe(self,instruction):
        utils.require_state(self.state,'default')
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        val = utils.validate_arg(instruction,'value',
                utils.validate_value,modifier=_modify_value)
        did = self.engine.observe(exp,val)
        self.observe_dict[did] = instruction
        return {"directive_id":did}

    def _do_predict(self,instruction):
        utils.require_state(self.state,'default')
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
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
    
    def _run_continuous_inference(self, step):
        while True:
            with self.continuous_inference_lock:
                if self.continuous_inference_running:
                    self.engine.infer(step)
                else: return
    
    def _do_start_continuous_inference(self,instruction):
        utils.require_state(self.state,'default')
        if not self.continuous_inference_running:
            self.continuous_inference_running = True
            thread.start_new_thread(CoreSivmLite._run_continuous_inference, (self, 1))
        return {}

    def _do_stop_continuous_inference(self,instruction):
        utils.require_state(self.state,'default')
        self.continuous_inference_running = False
        return {}

    def _do_continuous_inference_status(self,instruction):
        utils.require_state(self.state,'default')
        return {'running':self.engine.continuous_inference_running}
    
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
    return ob['value']

_symbol_map = { "add" : 'real_plus', "sub" : 'real_minus',
        "mul" : 'real_times', "div" : "real_div",
        "lt" : "real_lt", "gt" : "real_gt", "lte" : "real_lte",
        "gte": "real_gte", "eq" : "real_eq", "neq" : "real_neq",
        "symmetric_dirichlet_multinomial_make" : "make_sym_dir_mult",
        "condition_erp" : "branch",
        }
def _modify_symbol(s):
    if s in _symbol_map:
        s = _symbol_map[s]
    return s.encode('ascii')

_reverse_literal_type_map = dict((y,x) for x,y in _literal_type_map.items())

_python_to_venture_type_map = {
    bool: "boolean",
    int: "count",
    float: "number",
    list: "list",
    str: "string"
}

def _parse_value(val):
    if type(val) in _python_to_venture_type_map:
        return {"type": _python_to_venture_type_map[type(val)], "value": val}
    return {"type": "SP", "value": str(type(val))}
