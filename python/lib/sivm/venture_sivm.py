# -*- coding: utf-8 -*-

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

import copy
import cStringIO as StringIO

from venture.exception import VentureException
from venture.sivm import utils, macro, macro_system
import venture.value.dicts as v

class VentureSivm(object):

    def __init__(self, core_sivm):
        self.core_sivm = core_sivm
        self._do_not_annotate = False
        self._ci_pauser_stack = []
        self._clear()

    dicts = {
        'syntax_dict',
    }

    # list of all instructions supported by venture sivm
    _extra_instructions = {
        'force',
        'sample',
        'sample_all',
    }
    _core_instructions = {
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

    _dont_pause_continuous_inference = {
        'continuous_inference_status',
        'start_continuous_inference',
        'stop_continuous_inference',
    }

    def execute_instruction(self, instruction):
        utils.validate_instruction(instruction, self._core_instructions |
                                   self._extra_instructions)
        instruction_type = instruction['instruction']

        pause = instruction_type not in self._dont_pause_continuous_inference \
            and not self.core_sivm.engine.on_continuous_inference_thread()
        with self._pause_continuous_inference(pause=pause):
            if instruction_type == 'stop_continuous_inference':
                # It is possible for a paused CI to exist when
                # executing a stop ci instruction, because of the
                # 'endloop' inference SP.  To wit, the 'infer'
                # triggers a pause, and then the 'endloop' causes a
                # reentrant execute_instruction, which can land here.
                self._drop_top_paused_ci()
            if instruction_type in self._extra_instructions:
                f = getattr(self,'_do_'+instruction_type)
                return f(instruction)
            else:
                response = self._call_core_sivm_instruction(instruction)
                return response

    def _drop_top_paused_ci(self):
        candidate = len(self._ci_pauser_stack) - 1
        while candidate >= 0:
            if self._ci_pauser_stack[candidate].ci_was_running:
                self._ci_pauser_stack[candidate].ci_was_running = False
                break
            candidate -= 1

    ###############################
    # Reset stuffs
    ###############################

    def _clear(self):
        # Maps directive ids to the Syntax objects that record their
        # macro expansion history
        self.syntax_dict = {}

    ###############################
    # Serialization
    ###############################

    def save_io(self, stream, extra=None):
        if extra is None:
            extra = {}
        for d in self.dicts:
            extra[d] = getattr(self, d)
        return self.core_sivm.save_io(stream, extra)

    def load_io(self, stream):
        extra = self.core_sivm.load_io(stream)
        for d in self.dicts:
            setattr(self, d, extra[d])
        return extra

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
    # Sugars/desugars
    # for the CoreSivm instructions
    ###############################

    def _call_core_sivm_instruction(self,instruction):
        desugared_instruction = copy.copy(instruction)
        instruction_type = instruction['instruction']
        predicted_did = None
        # desugar the expression
        if instruction_type in [
                'assume',
                'define',
                'evaluate',
                'infer',
                'labeled_assume',
                'labeled_observe',
                'labeled_predict',
                'observe',
                'predict',
                'predict_all',
        ]:
            exp = utils.validate_arg(instruction,'expression',
                    utils.validate_expression, wrap_exception=False)
            syntax = macro_system.expand(exp)
            desugared_instruction['expression'] = syntax.desugared()
            # for error handling
            predicted_did = self._record_running_instruction(instruction, (exp, syntax))
        if instruction_type == 'forget':
            forgotten_did = instruction['directive_id']
        elif instruction_type == 'labeled_forget':
            label = utils.validate_arg(instruction, 'label',
                utils.validate_symbol)
            forgotten_did = self.core_sivm.engine.get_directive_id(label)
        else:
            forgotten_did = None
        try:
            response = self.core_sivm.execute_instruction(desugared_instruction)
        except VentureException as e:
            if self._do_not_annotate:
                raise
            import sys
            info = sys.exc_info()
            try:
                e = self._annotate(e, instruction)
            except Exception:
                print "Trying to annotate an exception at SIVM level led to:"
                import traceback
                print traceback.format_exc()
                raise e, None, info[2]
            finally:
                if instruction_type in ['define','assume','observe',
                        'predict','predict_all','evaluate','infer']:
                    # After annotation completes, clear the syntax
                    # dictionary, because the instruction was
                    # (presumably!) not recorded in the underlying
                    # engine (so e.g. future list_directives commands
                    # should not list it)
                    if predicted_did in self.syntax_dict:
                        del self.syntax_dict[predicted_did]
            raise e, None, info[2]
        self._register_executed_instruction(instruction, predicted_did,
            forgotten_did, response)
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
                return None
            else:
                # "infer" causes the engine to run a variant of the
                # actual passed expression.
                record = self._hack_infer_expression_structure(*record)
        if instruction_type is 'evaluate':
            record = self._hack_infer_expression_structure(*record, prefix="autorun")

        did = self.core_sivm.engine.predictNextDirectiveId()
        assert did not in self.syntax_dict
        self.syntax_dict[did] = record
        return did

    def _hack_infer_expression_structure(self, exp, syntax, prefix="run"):
        # The engine actually executes an application form around the
        # passed inference program.  Storing this will align the
        # indexes correctly.
        symbol = v.symbol(prefix)
        hacked_exp = [symbol, exp]
        hacked_syntax = macro.ListSyntax([macro.LiteralSyntax(symbol), syntax])
        return (hacked_exp, hacked_syntax)

    def _annotate(self, e, instruction):
        if e.exception == "evaluation":
            address = e.data['address'].asList()
            e.data['stack_trace'] = self.trace_address_to_stack(address)
            del e.data['address']
        # re-sugar the expression index
        if e.exception == 'parse':
            i = e.data['expression_index']
            exp = instruction['expression']
            i = macro_system.sugar_expression_index(exp,i)
            e.data['expression_index'] = i
        return e

    def trace_address_to_stack(self, address):
        return [frame for frame in [self._resugar(index) for index in address]
                if frame is not None]

    def _get_syntax_record(self, did):
        return self.syntax_dict[did]

    def _get_exp(self, did):
        return self._get_syntax_record(did)[0]

    def _resugar(self, index):
        did = index[0]
        if isinstance(did, basestring):
            # The object used at the top of "mem"s contains a string
            # in the location that usually holds dids.  Skip that
            # frame.
            return None
        if self._hack_skip_inference_prelude_entry(did):
            # The reason to skip is that those entries are (still)
            # never entered into the syntax_dict.
            print "Warning: skipping annotating did %s, assumed to be from the inference prelude" % did
            return None
        if self._hack_skip_synthetic_in_model_directive(index):
            # Engine.in_model synthesizes an extra directive, which is
            # not routed through here but can appear in stack traces.
            print "Warning: skipping annotating did %s, assumed to be synthesized by in_model" % did
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
        return self.core_sivm.engine.persistent_inference_trace \
            and did <= len(e._inference_prelude())

    def _hack_skip_synthetic_in_model_directive(self, index):
        # Actually, it may be sound to always skip indexes of length
        # 1, since they hardly carry any useful data anyway.  Could
        # instrument this check to see how often length-1 indexes are
        # annotatable.
        did = index[0]
        return did not in self.syntax_dict and len(index) == 1

    def _register_executed_instruction(self, instruction, predicted_did,
            forgotten_did, response):
        if response is not None and 'directive_id' in response:
            if response['directive_id'] != predicted_did:
                warning = "Warning: Instruction %s was pre-assigned did %s but actually assigned did %s"
                print warning % (instruction, predicted_did, response['directive_id'])
        elif predicted_did is not None:
            warning = "Warning: Instruction %s was pre-assigned did %s but not actually assigned any did"
            print warning % (instruction, predicted_did)
        instruction_type = instruction['instruction']
        # clear the dicts on the "clear" command
        if instruction_type == 'clear':
            self._clear()
        # forget directive mappings on the "forget" command
        if forgotten_did is not None:
            if forgotten_did in self.syntax_dict:
                del self.syntax_dict[forgotten_did]
            else:
                # XXX Presume that this is a fork-model directive id
                # collision as reported in Issue #586.
                pass
        if instruction_type in ['evaluate', 'infer']:
            # "evaluate" and "infer" are forgotten by the Engine;
            # forget them here, too.
            exp = utils.validate_arg(instruction,'expression',
                    utils.validate_expression, wrap_exception=False)
            if instruction_type is 'infer' and self.core_sivm.engine.is_infer_loop_program(exp):
                # We didn't save the infer loop thing
                pass
            else:
                # There is at least one way in which the predicted_did
                # may fail to be present in these dicts: if the
                # instruction being executed caused a "load" operation
                # (which mutates the current sivm!?).
                if predicted_did in self.syntax_dict:
                    del self.syntax_dict[predicted_did]

    ###############################
    # Continuous Inference Pauser
    ###############################

    def _pause_continuous_inference(self, pause=True):
        sivm = self # Naming conventions...
        class tmp(object):
            def __enter__(self):
                if pause:
                    self.ci_status = sivm._stop_continuous_inference()
                    self.ci_was_running = self.ci_status['running']
                else:
                    self.ci_was_running = False
                sivm._ci_pauser_stack.append(self)
            def __exit__(self, type, value, traceback):
                sivm._ci_pauser_stack.pop()
                if sivm._continuous_inference_status()['running']:
                    # The instruction started a new CI, so let it win
                    pass
                elif self.ci_was_running:
                    # print "restarting continuous inference"
                    sivm._start_continuous_inference(self.ci_status['expression'])
        return tmp()


    ###############################
    # Continuous Inference on/off
    ###############################

    def _continuous_inference_status(self):
        return self._call_core_sivm_instruction(
            {'instruction' : 'continuous_inference_status'})

    def _start_continuous_inference(self, expression):
        self._call_core_sivm_instruction(
            {'instruction' : 'start_continuous_inference',
             'expression' : expression})

    def _stop_continuous_inference(self):
        return self._call_core_sivm_instruction(
            {'instruction' : 'stop_continuous_inference'})

    ###############################
    # new instructions
    ###############################

    # adds label back to directive
    def _get_directive(self, did):
        import venture.lite.types as t
        directive = copy.copy(self.core_sivm.engine.model.traces.at_distinguished('directive', did))
        if directive[0] == 'define':
            ans = { 'instruction' : 'assume',
                    'symbol' : v.symbol(directive[1]),
                    'expression' : directive[2]
                }
        elif directive[0] == 'evaluate':
            ans = { 'instruction' : 'predict',
                    'expression' : directive[1]
                }
        else:
            assert directive[0] == 'observe'
            ans = { 'instruction' : 'observe',
                    'expression' : directive[1],
                    'value' : directive[2]
                }
        label = self.core_sivm.engine.get_directive_label(did)
        if label is not None:
            ans['label'] = v.symbol(label)
        ans['directive_id'] = did
        return ans

    def get_directive(self, did):
        with self._pause_continuous_inference():
            return self._get_directive(did)

    def list_directives(self):
        with self._pause_continuous_inference():
            dids = self.core_sivm.engine.model.traces.at_distinguished('dids')
            candidates = [self._get_directive(did) for did in sorted(dids)]
            return [c for c in candidates
                    if c['instruction'] in ['assume', 'observe', 'predict', 'predict_all']]

    def labeled_get_directive(self, label):
        label = utils.validate_symbol(label)
        did = self.core_sivm.engine.get_directive_id(label)
        return self.get_directive(did)

    def _do_force(self, instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression, wrap_exception=False)
        val = utils.validate_arg(instruction,'value',
                utils.validate_value)
        inst1 = {
                'instruction' : 'observe',
                'expression' : exp,
                'value' : val,
                }
        o1 = self._call_core_sivm_instruction(inst1)
        inst2 = { 'instruction' : 'infer',
                  'expression' : [v.symbol('incorporate')] }
        self._call_core_sivm_instruction(inst2)
        inst3 = {
                'instruction' : 'forget',
                'directive_id' : o1['directive_id'],
                }
        self._call_core_sivm_instruction(inst3)
        return {}

    def _do_sample(self, instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression, wrap_exception=False)
        inst1 = {
                'instruction' : 'predict',
                'expression' : exp,
                }
        o1 = self._call_core_sivm_instruction(inst1)
        inst2 = {
                'instruction' : 'forget',
                'directive_id' : o1['directive_id'],
                }
        self._call_core_sivm_instruction(inst2)
        return {'value':o1['value']}

    def _do_sample_all(self, instruction):
        exp = utils.validate_arg(instruction,'expression',
                utils.validate_expression, wrap_exception=False)
        inst1 = {
                'instruction' : 'predict_all',
                'expression' : exp,
                }
        o1 = self._call_core_sivm_instruction(inst1)
        inst2 = {
                'instruction' : 'forget',
                'directive_id' : o1['directive_id'],
                }
        self._call_core_sivm_instruction(inst2)
        return {'value':o1['value']}


    ###############################
    # Convenience wrappers some popular core instructions
    # Currently supported wrappers:
    # assume,observe,predict,forget,report,evaluate,infer,force,sample,list_directives
    ###############################

    def assume(self, name, expression, label=None):
        if label is None:
            d = {'instruction': 'assume', 'symbol':name, 'expression':expression}
        else:
            label = v.symbol(label)
            d = {'instruction': 'labeled_assume', 'symbol':name,
                 'expression':expression, 'label':label}
        return self.execute_instruction(d)

    def predict(self, expression, label=None):
        if label is None:
            d = {'instruction': 'predict', 'expression':expression}
        else:
            d = {'instruction': 'labeled_predict',
                 'expression':expression, 'label':v.symbol(label)}
        return self.execute_instruction(d)

    def observe(self, expression, value, label=None):
        if label is None:
            d = {'instruction': 'observe', 'expression':expression, 'value':value}
        else:
            d = {'instruction': 'labeled_observe', 'expression':expression,
                 'value':value, 'label':v.symbol(label)}
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

    def evaluate(self, params=None):
        d = {'instruction':'evaluate','params':params}
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
