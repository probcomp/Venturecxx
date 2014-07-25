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

from venture.exception import VentureException
from venture.sivm import utils
import copy

class CoreSivm(object):
    ###############################
    # public methods
    ###############################

    def __init__(self, engine):
        self.engine = engine
        self.state = 'default'
        # the engine doesn't support reporting "observe" directives
        self.observe_dict = {}
        self.profiler_enabled = False
    
    _implemented_instructions = {"assume","observe","predict",
            "configure","forget","freeze","report","infer",
            "clear","rollback","get_logscore","get_global_logscore",
            "start_continuous_inference","stop_continuous_inference",
            "continuous_inference_status", "profiler_configure"}
    
    def execute_instruction(self, instruction):
        utils.validate_instruction(instruction,self._implemented_instructions)
        f = getattr(self,'_do_'+instruction['instruction'])
        return f(instruction)

    ###############################
    # Serialization
    ###############################

    def save(self, fname, extra=None):
        if extra is None:
            extra = {}
        extra['observe_dict'] = self.observe_dict
        return self.engine.save(fname, extra)

    def load(self, fname):
        extra = self.engine.load(fname)
        self.observe_dict = extra['observe_dict']
        return extra

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
        return {"directive_id":did, "value":val}

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
        return {"directive_id":did, "value":val}

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

    def _do_freeze(self,instruction):
        utils.require_state(self.state,'default')
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_nonnegative_integer)
        self.engine.freeze(did)
        return {}

    def _do_report(self,instruction):
        utils.require_state(self.state,'default')
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_nonnegative_integer)
        if did in self.observe_dict:
            return {"value":copy.deepcopy(self.observe_dict[did]['value'])}
        else:
            val = self.engine.report_value(did)
            return {"value":val}

    def _do_infer(self,instruction):
        utils.require_state(self.state,'default')
        e = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        val = self.engine.infer_exp(e)
        return {"value":val}

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
        utils.require_state(self.state,'default')
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_nonnegative_integer)
        return {"logscore":self.engine.get_logscore(did)}

    def _do_get_global_logscore(self,_):
        utils.require_state(self.state,'default')
        l = self.engine.logscore()
        return {"logscore":l}
    
    ###########################
    # Continuous Inference
    ###########################
    
    def _do_continuous_inference_status(self,_):
        utils.require_state(self.state,'default')
        return self.engine.continuous_inference_status()

    def _do_start_continuous_inference(self,instruction):
        utils.require_state(self.state,'default')
        e = utils.validate_arg(instruction, 'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        self.engine.start_continuous_inference(e)
        
    def _do_stop_continuous_inference(self,_):
        utils.require_state(self.state,'default')
        self.engine.stop_continuous_inference()
    
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
    return expression

def _modify_value(ob):
    if ob['type'] in {'count', 'real'}:
        ans = copy.copy(ob)
        ans['type'] = 'number'
        return ans
    elif ob['type'] == 'atom':
        ans = copy.copy(ob)
        ans['value'] = int(ob['value'])
        return ans
    return ob

_symbol_map = {}

for s in ["lt", "gt", "lte", "gte"]:
    _symbol_map["int_" + s] = s

def _modify_symbol(s):
    if s in _symbol_map:
        s = _symbol_map[s]
    # NOTE: need to str() b/c unicode might come via REST,
    #       which the boost python wrappings can't convert
    return {"type": "symbol", "value": str(s)}

