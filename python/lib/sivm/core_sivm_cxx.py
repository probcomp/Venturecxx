#!/usr/bin/env python
# -*- coding: utf-8 -*-

from venture.exception import VentureException
from venture.sivm import utils
import json
import copy
from threading import Thread

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
        self.continuous_inference_thread = None
    
    def __del__(self):
        self._do_stop_continuous_inference(None)
    
    _implemented_instructions = {"assume","observe","predict",
            "configure","forget","report","infer",
            "clear","rollback","get_logscore","get_global_logscore",
            "start_continuous_inference","stop_continuous_inference",
            "continuous_inference_status", "profiler_configure"}
    
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
                utils.validate_symbol)
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
                utils.validate_nonnegative_integer,required=False)
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
                utils.validate_nonnegative_integer)
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
                utils.validate_nonnegative_integer)
        if did in self.observe_dict:
            return {"value":copy.deepcopy(self.observe_dict[did]['value'])}
        else:
            val = self.engine.report_value(did)
            return {"value":_parse_value(val)}

    def _do_infer(self,instruction):
        utils.require_state(self.state,'default')

        d = utils.validate_arg(instruction,'params',
                utils.validate_dict)
        # TODO FIXME figure out how to validate the arguments
        val = self.engine.infer(d)
        return {}

    def _do_clear(self,instruction):
        utils.require_state(self.state,'default')
        self.engine.clear()
        self.observe_dict = {}
        self.continuous_inference_running = False
        self.continuous_inference_thread = None
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
                utils.validate_nonnegative_integer)
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
    
    ###########################
    # Continuous Inference
    ###########################
    
    # no longer used; implemented in venture_sivm
    def _pause_continuous_inference(sivm):
        class tmp(object):
            def __enter__(temp):
                temp.was_continuous_inference_running = sivm.continuous_inference_running
                if temp.was_continuous_inference_running:
                    sivm._do_stop_continuous_inference(None)
            def __exit__(temp, type, value, traceback):
                if temp.was_continuous_inference_running:
                    sivm._do_start_continuous_inference(None)
        return tmp()
    
    def _run_continuous_inference(self, step):
        while self.continuous_inference_running:
            self.engine.infer({'transitions':step})
    
    def _do_start_continuous_inference(self,instruction):
        utils.require_state(self.state,'default')
        if not self.continuous_inference_running:
            self.continuous_inference_running = True
            self.continuous_inference_thread = Thread(target=CoreSivmCxx._run_continuous_inference, args=(self, 10))
            self.continuous_inference_thread.start()
        return {}
    
    def _do_stop_continuous_inference(self,instruction):
        utils.require_state(self.state,'default')
        self.continuous_inference_running = False
        if self.continuous_inference_thread != None:
            self.continuous_inference_thread.join()
            self.continuous_inference_thread = None
        return {}
    
    def _do_continuous_inference_status(self,instruction):
        utils.require_state(self.state,'default')
        return {'running':self.continuous_inference_running}
    
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
# These exist to bridge the gap
# between the cxx and the stack
###############################

def _modify_expression(expression):
    if isinstance(expression, basestring):
        return _modify_symbol(expression)
    if isinstance(expression, (list,tuple)):
        return map(_modify_expression, expression)
    if isinstance(expression, dict):
        return _modify_value(expression)

def _modify_value(ob):
    if ob['type'] in {'count', 'real'}:
        ob['type'] = 'number'
    elif ob['type'] == 'atom':
        ob['value'] = int(ob['value'])
    return ob

_symbol_map = { 
    "add" : 'plus', 
    "sub" : 'minus', 
    "mul" : 'times',
    "symmetric_dirichlet_multinomial_make" : "make_sym_dir_mult",
    "condition_erp" : "biplex", 
    "crp_make" : "make_crp",
    "dirichlet_multinomial_make" : "make_dir_mult",
    "beta_bernoulli_make" : "make_beta_bernoulli",
}

def _modify_symbol(s):
    if s in _symbol_map:
        s = _symbol_map[s]
    # NOTE: need to str() b/c unicode might come via REST,
    #       which the boost python wrappings can't convert
    return {"type": "symbol", "value": str(s)}

def _parse_value(val):
    return val
