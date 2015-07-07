# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

from venture.exception import VentureException
from venture.sivm import utils, macro, macro_system
import venture.value.dicts as v

class VentureSivm(object):

    def __init__(self, core_sivm):
        self.core_sivm = core_sivm
        self._clear()
        self._init_continuous_inference()

    dicts = [s + '_dict' for s in ['breakpoint', 'label', 'did', 'syntax', 'directive']]

    # list of all instructions supported by venture sivm
    _extra_instructions = {'labeled_assume','labeled_observe',
            'labeled_predict','labeled_forget','labeled_freeze','labeled_report',
            'list_directives','get_directive','labeled_get_directive',
            'force','sample','get_current_exception',
            'get_state', 'reset', 'debugger_list_breakpoints','debugger_get_breakpoint'}
    _core_instructions = {"define","assume","observe","predict",
            "configure","forget","freeze","report","infer","start_continuous_inference",
            "stop_continuous_inference","continuous_inference_status",
            "clear","rollback","get_global_logscore",
            "debugger_configure","debugger_list_random_choices", "debugger_clear",
            "debugger_force_random_choice","debugger_report_address",
            "debugger_history","debugger_dependents","debugger_address_to_source_code_location",
            "debugger_set_breakpoint_address","debugger_set_breakpoint_source_code_location",
            "debugger_remove_breakpoint","debugger_continue","profiler_configure",
            "profiler_clear","profiler_list_random_choices",
            "profiler_address_to_source_code_location","profiler_get_random_choice_acceptance_rate",
            "profiler_get_global_acceptance_rate","profiler_get_random_choice_proposal_time",
            "profiler_get_global_proposal_time"}

    _dont_pause_continuous_inference = {"start_continuous_inference",
            "stop_continuous_inference", "continuous_inference_status"}

    def execute_instruction(self, instruction):
        utils.validate_instruction(instruction,self._core_instructions | self._extra_instructions)
        instruction_type = instruction['instruction']

        pause = instruction_type not in self._dont_pause_continuous_inference and not self.core_sivm.engine.on_continuous_inference_thread()
        with self._pause_continuous_inference(pause=pause):
            if instruction_type in self._extra_instructions:
                f = getattr(self,'_do_'+instruction_type)
                return f(instruction)
            else:
                response = self._call_core_sivm_instruction(instruction)
                return response

    ###############################
    # Reset stuffs
    ###############################

    def _clear(self):
        self.label_dict = {} # Maps labels to directive ids
        self.did_dict = {} # Maps directive ids back to labels
        self.directive_dict = {} # Maps directive ids to the actual instructions
        self.syntax_dict = {} # Maps directive ids to the Syntax objects that record their macro expansion history
        self._debugger_clear()
        self.state = 'default'
        self.attempted = [] # Stores Syntax objects of in-progress instructions (that do not have assigned directive IDs yet).

    def _debugger_clear(self):
        self.breakpoint_dict = {}

    ###############################
    # Serialization
    ###############################

    def save(self, fname, extra=None):
        if extra is None:
            extra = {}
        for d in self.dicts:
            extra[d] = getattr(self, d)
        return self.core_sivm.save(fname, extra)

    def load(self, fname):
        extra = self.core_sivm.load(fname)
        for d in self.dicts:
            setattr(self, d, extra[d])
        return extra

    ###############################
    # Sugars/desugars
    # for the CoreSivm instructions
    ###############################

    def _call_core_sivm_instruction(self,instruction):
        desugared_instruction = copy.copy(instruction)
        instruction_type = instruction['instruction']
        # desugar the expression
        if instruction_type in ['define','assume','observe','predict','infer']:
            exp = utils.validate_arg(instruction,'expression',
                    utils.validate_expression, wrap_exception=False)
            syntax = macro_system.expand(exp)
            desugared_instruction['expression'] = syntax.desugared()
            # for error handling
            self._record_running_instruction(instruction, (exp, syntax))
        # desugar the expression index
        if instruction_type == 'debugger_set_breakpoint_source_code_location':
            desugared_src_location = desugared_instruction['source_code_location']
            did = desugared_src_location['directive_id']
            old_index = desugared_src_location['expression_index']
            exp = self.directive_dict[did]['expression']
            new_index = macro_system.desugar_expression_index(exp, old_index)
            desugared_src_location['expression_index'] = new_index
        try:
            response = self.core_sivm.execute_instruction(desugared_instruction)
        except VentureException as e:
            # raise # One can suppress error annotation by uncommenting this
            import sys
            info = sys.exc_info()
            try:
                e = self._annotate(e, instruction)
            except Exception as e2:
                print "Trying to annotate an exception at SIVM level led to:"
                import traceback
                print traceback.format_exc()
                raise e, None, info[2]
            raise e, None, info[2]
        self._register_executed_instruction(instruction, response)
        return response

    def _record_running_instruction(self, instruction, record):
        # This is a crock.  I am trying to ballistically coordinate
        # the expressions and Syntax objects I record here with the
        # expressions the underlying Engine actually evaluates in its
        # traces.
        instruction_type = instruction['instruction']
        if instruction_type is 'infer':
            if self.core_sivm.engine.is_infer_loop_program(record[0]):
                # The engine does something funny with infer loop that
                # has the effect that I should not store the loop
                # infer program itself.
                pass
            else:
                assert len(self.attempted) == 0, "Infer should never reentrantly run itself."
                self.attempted.append(self._hack_infer_expression_structure(*record))
        else:
            # One might think this should be done for 'infer' too.  As
            # long as there is no mutation and SPs cannot roundtrip
            # through the stack dict representation, I expect there to
            # be no way for a stack trace to reference an 'infer'
            # (rather than 'define') command directly (as opposed to
            # model statements introduced thereby, which are handled
            # separately) after the dynamic extent of that 'infer'.
            # That means it's currently safe to leave it off.  Why not
            # put it in anyway?  Inertia.
            did = self.core_sivm.engine.predictNextDirectiveId()
            assert did not in self.syntax_dict
            tmp_instruction = {}
            tmp_instruction['directive_id'] = did
            for key in ('instruction', 'expression', 'symbol', 'value'):
                if key in instruction:
                    tmp_instruction[key] = copy.copy(instruction[key])
            self.directive_dict[did] = tmp_instruction
            self.syntax_dict[did] = record

    def _hack_infer_expression_structure(self, exp, syntax):
        # The engine actually executes an application form around the
        # passed inference program.  Storing this will align the
        # indexes correctly.
        symbol = v.symbol("run")
        hacked_exp = [symbol, exp]
        hacked_syntax = macro.ListSyntax([macro.LiteralSyntax(symbol), syntax])
        return (hacked_exp, hacked_syntax)

    def _annotate(self, e, instruction):
        if e.exception == "evaluation":
            self.state='exception'

            address = e.data['address'].asList()
            e.data['stack_trace'] = self.trace_address_to_stack(address)
            del e.data['address']

            self.current_exception = e.to_json_object()
        if e.exception == "breakpoint":
            self.state='paused'
            self.current_exception = e.to_json_object()
        # re-sugar the expression index
        if e.exception == 'parse':
            i = e.data['expression_index']
            exp = instruction['expression']
            i = macro_system.sugar_expression_index(exp,i)
            e.data['expression_index'] = i
        # turn directive_id into label
        if e.exception == 'invalid_argument':
            if e.data['argument'] == 'directive_id':
                did = e.data['directive_id']
                if did in self.did_dict:
                    e.data['label'] = self.did_dict[did]
                    e.data['argument'] = 'label'
                    del e.data['directive_id']
        return e

    def trace_address_to_stack(self, address):
        return [frame for frame in [self._resugar(index) for index in address] if frame is not None]

    def _get_syntax_record(self, did):
        if did not in self.syntax_dict:
            # print "Assuming missing did %s is from the top of the stack %s" % (did, self.attempted)
            # Presume that the desired did is currently being evaluated
            self.syntax_dict[did] = self.attempted.pop()
        return self.syntax_dict[did]

    def _get_exp(self, did):
        return self._get_syntax_record(did)[0]

    def _resugar(self, index):
        did = index[0]
        if not did:
            # The empty address used at the top of "mem"s contains the
            # empty list in the location that usually holds dids.
            # Skip that frame.
            return None
        if self._hack_skip_inference_prelude_entry(did):
            # The reason to skip is to avoid popping the
            # self.attempted stack even though the did is not there.
            print "Warning: skipping annotating did %s, assumed to be from the inference prelude" % did
            return None
        exp, syntax = self._get_syntax_record(did)
        index = index[1:]

        return dict(
          exp = exp,
          did = did,
          index = syntax.resugar_index(index)
        )

    def _hack_skip_inference_prelude_entry(self, did):
        import venture.engine.engine as e
        # <= because directive IDs are 1-indexed (see Engine.nextBaseAddr)
        return self.core_sivm.engine.persistent_inference_trace and did <= len(e._inference_prelude())

    def _register_executed_instruction(self, instruction, response):
        instruction_type = instruction['instruction']
        # clear the dicts on the "clear" command
        if instruction_type == 'clear':
            self._clear()
        # forget directive mappings on the "forget" command
        if instruction_type == 'forget':
            did = instruction['directive_id']
            del self.directive_dict[did]
            del self.syntax_dict[did]
            if did in self.did_dict:
                del self.label_dict[self.did_dict[did]]
                del self.did_dict[did]
        if instruction_type in ['infer']:
            # Don't build up "in-flight" records, even though "infer"
            # is not recorded for posterity.
            # TODO Is there a race condition here?  The continuous
            # inference thread repeatedly calls ripl.infer, which will
            # trigger both pushes to self.attempted and pops from it.
            # If some other ripl instruction happens concurrently that
            # also affects self.attempted, could there be a mix-up?
            # Or does pausing continuous inference prevent that from
            # happening?  Should I make the attempt stack thread-local
            # defensively anyway?
            exp = utils.validate_arg(instruction,'expression',
                    utils.validate_expression, wrap_exception=False)
            if self.core_sivm.engine.is_infer_loop_program(exp):
                # We didn't save the infer loop thing
                pass
            else:
                self.attempted.pop()
        # save the breakpoint if the instruction sets the breakpoint
        if instruction_type in ['debugger_set_breakpoint_address',
                'debugger_set_breakpoint_source_code_location']:
            bid = response['breakpoint_id']
            tmp_instruction = copy.copy(instruction)
            tmp_instruction['breakpoint_id'] = bid
            del tmp_instruction['instruction']
            self.breakpoint_dict[bid] = tmp_instruction

    ###############################
    # Continuous Inference Pauser
    ###############################

    def _pause_continuous_inference(self, pause=True):
        sivm = self # Naming conventions...
        class tmp(object):
            def __enter__(self):
                self.ci_status = sivm._continuous_inference_status()
                self.ci_was_running = pause and self.ci_status["running"]
                if self.ci_was_running:
                    sivm._stop_continuous_inference()
            def __exit__(self, type, value, traceback):
                if sivm._continuous_inference_status()["running"]:
                    # The instruction started a new CI, so let it win
                    pass
                elif self.ci_was_running:
                    # print "restarting continuous inference"
                    sivm._start_continuous_inference(self.ci_status["expression"])
        return tmp()


    ###############################
    # Continuous Inference on/off
    ###############################

    def _init_continuous_inference(self):
        pass

    def _continuous_inference_status(self):
        return self._call_core_sivm_instruction({"instruction" : "continuous_inference_status"})

    def _start_continuous_inference(self, expression):
        self._call_core_sivm_instruction({"instruction" : "start_continuous_inference", "expression" : expression})

    def _stop_continuous_inference(self):
        self._call_core_sivm_instruction({"instruction" : "stop_continuous_inference"})

    ###############################
    # Shortcuts
    ###############################

    def _validate_label(self, instruction, exists=False):
        label = utils.validate_arg(instruction,'label',
                utils.validate_symbol)
        if exists==False and label in self.label_dict:
            raise VentureException('invalid_argument',
                    'Label "{}" is already assigned to a different directive.'.format(label),
                    argument='label')
        if exists==True and label not in self.label_dict:
            raise VentureException('invalid_argument',
                    'Label "{}" does not exist.'.format(label),
                    argument='label')
        return label

    ###############################
    # labeled instruction wrappers
    ###############################

    def _do_labeled_directive(self, instruction):
        label = self._validate_label(instruction, exists=False)
        tmp = instruction.copy()
        tmp['instruction'] = instruction['instruction'][len('labeled_'):]
        del tmp['label']
        response = self._call_core_sivm_instruction(tmp)
        did = response['directive_id']
        self.label_dict[label] = did
        self.did_dict[did] = label
        return response

    _do_labeled_assume = _do_labeled_directive
    _do_labeled_observe = _do_labeled_directive
    _do_labeled_predict = _do_labeled_directive

    def _do_labeled_operation(self, instruction):
        label = self._validate_label(instruction, exists=True)
        tmp = instruction.copy()
        tmp['instruction'] = instruction['instruction'][len('labeled_'):]
        tmp['directive_id'] = self.label_dict[label]
        del tmp['label']
        return self._call_core_sivm_instruction(tmp)

    _do_labeled_forget = _do_labeled_operation
    _do_labeled_freeze = _do_labeled_operation
    _do_labeled_report = _do_labeled_operation

    ###############################
    # new instructions
    ###############################

    # adds label back to directive
    def get_directive(self, did):
        tmp = copy.copy(self.directive_dict[did])
        if did in self.did_dict:
            tmp['label'] = v.symbol(self.did_dict[did])
            #tmp['instruction'] = 'labeled_' + tmp['instruction']
        return tmp

    def _do_list_directives(self, _):
        candidates = [self.get_directive(did) for did in sorted(self.directive_dict.keys())]
        return { "directives" : [c for c in candidates if c['instruction'] in ['assume', 'observe', 'predict']] }

    def _do_get_directive(self, instruction):
        did = utils.validate_arg(instruction, 'directive_id', utils.validate_positive_integer)
        if not did in self.directive_dict:
            raise VentureException('invalid_argument',
                    "Directive with directive_id = {} does not exist".format(did),
                    argument='directive_id')
        return {"directive": self.get_directive(did)}

    def _do_labeled_get_directive(self, instruction):
        label = self._validate_label(instruction, exists=True)
        did = self.label_dict[label]
        return {"directive":self.get_directive(did)}

    def _do_force(self, instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression, wrap_exception=False)
        val = utils.validate_arg(instruction,'value',
                utils.validate_value)
        inst1 = {
                "instruction" : "observe",
                "expression" : exp,
                "value" : val,
                }
        o1 = self._call_core_sivm_instruction(inst1)
        inst2 = { "instruction" : "infer",
                  "expression" : [v.symbol("incorporate")] }
        self._call_core_sivm_instruction(inst2)
        inst3 = {
                "instruction" : "forget",
                "directive_id" : o1['directive_id'],
                }
        self._call_core_sivm_instruction(inst3)
        return {}

    def _do_sample(self, instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression, wrap_exception=False)
        inst1 = {
                "instruction" : "predict",
                "expression" : exp,
                }
        o1 = self._call_core_sivm_instruction(inst1)
        inst2 = {
                "instruction" : "forget",
                "directive_id" : o1['directive_id'],
                }
        self._call_core_sivm_instruction(inst2)
        return {"value":o1['value']}

    # not used anymore?
    def _do_continuous_inference_configure(self, instruction):
        d = utils.validate_arg(instruction,'options',
                utils.validate_dict, required=False)
        enable_ci = utils.validate_arg(d,'continuous_inference_enable',
                utils.validate_boolean, required=False)
        if enable_ci != None:
            if enable_ci == True and self._continuous_inference_enabled() == False:
                self._enable_continuous_inference()
            if enable_ci == False and self._continuous_inference_enabled() == True:
                self._disable_continuous_inference()
        return {"options":{
                "continuous_inference_enable" : self._continuous_inference_enabled(),
                }}

    def _do_get_current_exception(self, _):
        utils.require_state(self.state,'exception','paused')
        return {
                'exception': copy.deepcopy(self.current_exception),
                }

    def _do_get_state(self, _):
        return {
                'state': self.state,
                }

    def _do_reset(self, instruction):
        if self.state != 'default':
            instruction = {
                    'instruction': 'rollback',
                    }
            self._call_core_sivm_instruction(instruction)
        instruction = {
                'instruction': 'clear',
                }
        self._call_core_sivm_instruction(instruction)
        return {}

    def _do_debugger_list_breakpoints(self, _):
        return {
                "breakpoints" : copy.deepcopy(self.breakpoint_dict.values()),
                }

    def _do_debugger_get_breakpoint(self, instruction):
        bid = utils.validate_arg(instruction,'breakpoint_id',
                utils.validate_positive_integer)
        if not bid in self.breakpoint_dict:
            raise VentureException('invalid_argument',
                    "Breakpoint with breakpoint_id = {} does not exist".format(bid),
                    argument='breakpoint_id')
        return {"breakpoint":copy.deepcopy(self.breakpoint_dict[bid])}


    ###############################
    # Convenience wrappers some popular core instructions
    # Currently supported wrappers:
    # assume,observe,predict,forget,report,infer,force,sample,list_directives
    ###############################

    def assume(self, name, expression, label=None):
        if label==None:
            d = {'instruction': 'assume', 'symbol':name, 'expression':expression}
        else:
            label = v.symbol(label)
            d = {'instruction': 'labeled_assume', 'symbol':name, 'expression':expression,'label':label}
        return self.execute_instruction(d)

    def predict(self, expression, label=None):
        if label==None:
            d = {'instruction': 'predict', 'expression':expression}
        else:
            d = {'instruction': 'labeled_predict', 'expression':expression,'label':v.symbol(label)}
        return self.execute_instruction(d)

    def observe(self, expression, value, label=None):
        if label==None:
            d = {'instruction': 'observe', 'expression':expression, 'value':value}
        else:
            d = {'instruction': 'labeled_observe', 'expression':expression, 'value':value, 'label':v.symbol(label)}
        return self.execute_instruction(d)

    def forget(self, label_or_did):
        if isinstance(label_or_did,int):
            d = {'instruction':'forget','directive_id':label_or_did}
        else:
            d = {'instruction':'labeled_forget','label':v.symbol(label_or_did)}
        return self.execute_instruction(d)

    def report(self, label_or_did):
        if isinstance(label_or_did,int):
            d = {'instruction':'report','directive_id':label_or_did}
        else:
            d = {'instruction':'labeled_report','label':v.symbol(label_or_did)}
        return self.execute_instruction(d)

    def infer(self, params=None):
        d = {'instruction':'infer','params':params}
        return self.execute_instruction(d)

    def force(self, expression, value):
        d = {'instruction':'force','expression':expression, 'value':value}
        return self.execute_instruction(d)

    def sample(self, expression):
        d = {'instruction':'sample','expression':expression}
        return self.execute_instruction(d)

    def list_directives(self): return self.execute_instruction({'instruction':'list_directives'})
