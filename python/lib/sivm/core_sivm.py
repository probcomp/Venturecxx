# Copyright (c) 2013, 2014, 2015, 2016 MIT Probabilistic Computing Project.
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

import copy
import cStringIO as StringIO

from venture.exception import VentureException
from venture.sivm import utils
import venture.value.dicts as v

class CoreSivm(object):
    ###############################
    # public methods
    ###############################

    def __init__(self, engine):
        self.engine = engine
        self.profiler_enabled = False

    _implemented_instructions = {
        'assume',
        'clear',
        'continuous_inference_status',
        'define',
        'evaluate',
        'forget',
        'freeze',
        'infer',
        'labeled_assume',
        'labeled_forget',
        'labeled_freeze',
        'labeled_observe',
        'labeled_predict',
        'labeled_report',
        'observe',
        'predict',
        'predict_all',
        'report',
        'start_continuous_inference',
        'stop_continuous_inference',
    }

    def execute_instruction(self, instruction):
        utils.validate_instruction(instruction,self._implemented_instructions)
        f = getattr(self,'_do_'+instruction['instruction'])
        return f(instruction)

    ###############################
    # Serialization
    ###############################

    def save_io(self, stream, extra=None):
        if extra is None:
            extra = {}
        return self.engine.save_io(stream, extra)

    def load_io(self, stream):
        return self.engine.load_io(stream)

    def save(self, fname, extra=None):
        with open(fname, 'w') as fp:
            self.save_io(fp, extra=extra)

    def saves(self, extra=None):
        ans = StringIO.StringIO()
        self.save_io(ans, extra=extra)
        return ans.getvalue()

    def load(self, fname):
        with open(fname) as fp:
            return self.load_io(fp)

    def loads(self, string):
        return self.load_io(StringIO.StringIO(string))

    ###############################
    # Instruction implementations
    ###############################

    def _do_define(self,instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        sym = utils.validate_arg(instruction,'symbol',
                utils.validate_symbol)
        (did, val) = self.engine.define(sym,exp)
        return {"directive_id":did, "value":val}

    #FIXME: remove the modifier arguments in new implementation
    def _do_assume(self,instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        sym = utils.validate_arg(instruction,'symbol',
                utils.validate_symbol)
        did, val = self.engine.assume(sym,exp)
        return {"directive_id":did, "value":val}

    def _do_labeled_assume(self, instruction):
        exp = utils.validate_arg(instruction, 'expression',
                utils.validate_expression, modifier=_modify_expression,
                wrap_exception=False)
        sym = utils.validate_arg(instruction, 'symbol', utils.validate_symbol)
        label = utils.validate_arg(instruction, 'label', utils.validate_symbol)
        did, val = self.engine.labeled_assume(label, sym, exp)
        return {'directive_id': did, 'value': val}

    def _do_observe(self,instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        val = utils.validate_arg(instruction,'value',
                utils.validate_value,modifier=_modify_value)
        did, weights = self.engine.observe(exp,val)
        return {"directive_id":did, "value":weights}

    def _do_labeled_observe(self, instruction):
        exp = utils.validate_arg(instruction, 'expression',
                utils.validate_expression, modifier=_modify_expression,
                wrap_exception=False)
        val = utils.validate_arg(instruction, 'value', utils.validate_value,
                modifier=_modify_value)
        label = utils.validate_arg(instruction, 'label', utils.validate_symbol)
        did, weights = self.engine.labeled_observe(label, exp, val)
        return {'directive_id': did, 'value': weights}

    def _do_predict(self,instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        did, val = self.engine.predict(exp)
        return {"directive_id":did, "value":val}

    def _do_labeled_predict(self, instruction):
        exp = utils.validate_arg(instruction, 'expression',
                utils.validate_expression, modifier=_modify_expression,
                wrap_exception=False)
        label = utils.validate_arg(instruction, 'label', utils.validate_symbol)
        did, val = self.engine.labeled_predict(label, exp)
        return {'directive_id': did, 'value': val}

    def _do_predict_all(self,instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        did, val = self.engine.predict_all(exp)
        return {"directive_id":did, "value":val}

    def _do_forget(self,instruction):
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_nonnegative_integer)
        weights = self.engine.forget(did)
        return {"value": weights}

    def _do_labeled_forget(self, instruction):
        label = utils.validate_arg(instruction, 'label', utils.validate_symbol)
        weights = self.engine.labeled_forget(label)
        return {'value': weights}

    def _do_freeze(self,instruction):
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_nonnegative_integer)
        self.engine.freeze(did)
        return {}

    def _do_labeled_freeze(self, instruction):
        label = utils.validate_arg(instruction, 'label', utils.validate_symbol)
        self.engine.labeled_freeze(label)
        return {}

    def _do_report(self,instruction):
        did = utils.validate_arg(instruction,'directive_id',
                utils.validate_nonnegative_integer)
        return {"value": self.engine.report_value(did)}

    def _do_labeled_report(self, instruction):
        label = utils.validate_arg(instruction, 'label', utils.validate_symbol)
        value = self.engine.labeled_report_value(label)
        return {'value': value}

    def _do_evaluate(self,instruction):
        e = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        (did, val) = self.engine.evaluate(e)
        return {"directive_id": did, "value":val}

    def _do_infer(self,instruction):
        e = utils.validate_arg(instruction,'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        (did, val) = self.engine.infer(e)
        return {"directive_id": did, "value":val}

    def _do_clear(self,_):
        self.engine.clear()
        return {}

    ###########################
    # Continuous Inference
    ###########################

    def _do_continuous_inference_status(self,_):
        return self.engine.continuous_inference_status()

    def _do_start_continuous_inference(self,instruction):
        e = utils.validate_arg(instruction, 'expression',
                utils.validate_expression,modifier=_modify_expression, wrap_exception=False)
        self.engine.start_continuous_inference(e)

    def _do_stop_continuous_inference(self,_):
        return self.engine.stop_continuous_inference()

    ##############################
    # Profiler
    ##############################

    def profiler_running(self, enable=None):
        old_state = self.profiler_enabled
        if enable is not None:
            self.profiler_enabled = enable
            self.engine.set_profiling(enable)
        return old_state

###############################
# Input modification
###############################

# Convert any bare basestrings to stack dicts (symbols)
# Convert all symbol names to Python strings from unicode

def _modify_expression(expression):
    if isinstance(expression, basestring):
        return _modify_symbol(expression)
    if isinstance(expression, (list,tuple)):
        return map(_modify_expression, expression)
    if isinstance(expression, dict):
        return _modify_value(expression)
    return expression

def _modify_value(ob):
    if ob['type'] in ['symbol', 'string']:
        # Unicode hack for the same reason as in _modify_symbol
        ans = copy.copy(ob)
        ans['value'] = str(ob['value'])
        return ans
    return ob

def _modify_symbol(s):
    # NOTE: need to str() b/c unicode might come via REST,
    #       which the boost python wrappings can't convert
    return v.symbol(str(s))
