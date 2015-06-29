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

'''The Read, Infer, Predict Layer.

The RIPL is the primary interface to using Venture as a Python
library.  One object of the Ripl class represents a distinct Venture
session and offers a programmatic interface to the underlying Venture
Stochastic Inference Virtual Machine (SIVM).  The remainder of this
document assumes a basic familiarity with the Venture language and
programming model.

The methods of Ripl generally correspond to Venture instructions.  Any
necessary expressions can be passed in either as strings in concrete
Venture syntax or as Python objects in abstract Venture syntax, or a
mixture of both.  Providing pre-parsed instructions is more efficient
(Venture's under-optimized parser currently imposes significant
overhead), but strings in concrete syntax are likely to be more
readable.

Typical usage begins by using one of the factory functions in the
`venture.shortcuts` module::

    import venture.shortcuts as s
    r = s.Lite().make_church_prime_ripl()
    # r is a fresh Ripl
    r.assume(...)
    r.observe(...)
    r.infer(...)

'''

import numbers
import re
from os import path
import numpy as np

from venture.exception import VentureException
from venture.lite.value import VentureValue
import plugins
import utils as u
import venture.value.dicts as v

from venture.lite.node import RequestNode, OutputNode # For scaffold drawing

PRELUDE_FILE = 'prelude.vnt'

class Ripl():
    '''The Read, Infer, Predict Layer of one running Venture instance.'''

    def __init__(self,sivm,parsers):
        self.sivm = sivm
        self.parsers = parsers
        self.directive_id_to_stringable_instruction = {}
        self.directive_id_to_mode = {}
        self.mode = parsers.keys()[0]
        self._n_prelude = 0
        # TODO Loading the prelude currently (6/26/14) slows the test suite to a crawl
        # self.load_prelude()
        r = self.sivm.core_sivm.engine.ripl
        if r is None:
            self.sivm.core_sivm.engine.ripl = self
        elif r is self:
            # OK
            pass
        else:
            print "Wrapping sivm %s in a new ripl but it already has one: %s.  Engine to ripl references may be incorrect." % (self.sivm, r)
        plugins.__venture_start__(self)


    ############################################
    # Languages
    ############################################

    def get_mode(self):
        return self.mode

    def list_available_modes(self):
        return self.parsers.keys()

    def set_mode(self, mode):
        if mode in self.parsers:
            self.mode = mode
        else:
            raise VentureException('invalid_mode',
                    "Mode {} is not implemented by this RIPL".format(mode))

    ############################################
    # Backend
    ############################################

    def backend(self):
        '''Return the name of backend powering this Ripl.  Either ``"lite"`` or ``"puma"``.'''
        return self.sivm.core_sivm.engine.model.backend.name()

    ############################################
    # Execution
    ############################################



    def execute_instruction(self, instruction=None, params=None, suppress_pausing_continous_inference=False):
        # The suppress_pausing_continous_inference flag is used by the
        # thread doing the continuous inference.
        p = self._cur_parser()
        try: # execute instruction, and handle possible exception
            # perform parameter substitution if necessary
            if isinstance(instruction, basestring):
                if params != None:
                    stringable_instruction = self.substitute_params(instruction,params)
                else:
                    stringable_instruction = instruction
                # parse instruction
                parsed_instruction = p.parse_instruction(stringable_instruction)
            else:
                stringable_instruction = instruction
                parsed_instruction = self._ensure_parsed(instruction)
            # if directive, then save the text string
            if parsed_instruction['instruction'] in ['assume', 'observe', 'predict', 'define',
                                                     'labeled_assume','labeled_observe','labeled_predict']:
                did = self.sivm.core_sivm.engine.predictNextDirectiveId()
                self.directive_id_to_stringable_instruction[did] = stringable_instruction
                self.directive_id_to_mode[did] = self.mode
            ret_value = self.sivm.execute_instruction(parsed_instruction, suppress_pausing_continous_inference=suppress_pausing_continous_inference)
        except VentureException as e:
            import sys
            info = sys.exc_info()
            try:
                annotated = self._annotated_error(e, instruction)
            except Exception as e2:
                print "Trying to annotate an exception led to:"
                import traceback
                print traceback.format_exc()
                e.annotated = False
                raise e, None, info[2]
            raise annotated, None, info[2]
        return ret_value

    def _annotated_error(self, e, instruction):
        if e.exception is 'evaluation':
            p = self._cur_parser()
            for i, frame in enumerate(e.data['stack_trace']):
                exp, text_index = self.humanReadable(**frame)
                e.data['stack_trace'][i] = {
                    'expression_string' : exp,
                    'text_index' : text_index,
                }
            e.annotated = True
            return e

        # TODO This error reporting is broken for ripl methods,
        # because the computed text chunks refer to the synthetic
        # instruction string instead of the actual data the caller
        # passed.
        instruction_string = self._ensure_unparsed(instruction)

        p = self._cur_parser()
        # all exceptions raised by the Sivm get augmented with a
        # text index (which defaults to the entire instruction)
        if 'text_index' not in e.data:
            e.data['text_index'] = [0,len(instruction_string)-1]

        # in the case of a parse exception, the text_index gets narrowed
        # down to the exact expression/atom that caused the error
        if e.exception == 'parse':
            # calculate the positions of the arguments
            args, arg_ranges = p.split_instruction(instruction_string)
            try:
                text_index = self._cur_parser().expression_index_to_text_index(
                        args['expression'], e.data['expression_index'])
                offset = arg_ranges['expression'][0]
                text_index = [x + offset for x in text_index]
            except VentureException as e2:
                if e2.exception == 'no_text_index': text_index = None
                else: raise
            e.data['text_index'] = text_index

        # for "text_parse" exceptions, even trying to split the instruction
        # results in an exception
        if e.exception == 'text_parse':
            try:
                p.parse_instruction(instruction_string)
            except VentureException as e2:
                assert e2.exception == 'text_parse'
                e = e2

        # in case of invalid argument exception, the text index
        # refers to the argument's location in the string
        if e.exception == 'invalid_argument':
            # calculate the positions of the arguments
            args, arg_ranges = p.split_instruction(instruction_string)
            arg = e.data['argument']
            text_index = arg_ranges[arg]
            e.data['text_index'] = text_index

        a = e.data['text_index'][0]
        b = e.data['text_index'][1]+1
        e.data['text_snippet'] = instruction_string[a:b]
        e.data['instruction_string'] = instruction_string

        e.annotated = True
        return e

    def parse_program(self, program_string, params=None):
        p = self._cur_parser()
        # perform parameter substitution if necessary
        if params != None:
            program_string = self.substitute_params(program_string,params)
        # TODO the right thing is to make "comment" a valid instruction type.
        if self.get_mode() == "church_prime":
            start_comment_regex = ";"
        elif self.get_mode() == "venture_script":
            start_comment_regex = "//"
        else:
            raise Exception("Do not know comment syntax for mode {}".format(self.get_mode()))
        no_comments = '\n'.join(re.split(start_comment_regex, x)[0] for x in program_string.split('\n'))
        instructions, positions = p.split_program(no_comments)
        return [self._ensure_parsed(i) for i in instructions], positions

    def execute_program(self, program_string, params=None):
        return self.execute_parsed_program(*self.parse_program(program_string, params=params))

    def execute_parsed_program(self, instructions, _positions):
        vals = []
        for instruction in instructions:
            if instruction['instruction'] == "load":
                vals.append(self.execute_program_from_file(instruction["file"]))
            else:
                vals.append(self.execute_instruction(instruction))
        return vals

    def execute_program_from_file(self, filename):
        _, ext = path.splitext(filename)
        old_mode = self.get_mode()
        if ext == ".vnts":
            self.set_mode("venture_script")
        else:
            self.set_mode("church_prime")
        try:
            with open(filename) as f:
                self.execute_program(f.read())
        finally:
            self.set_mode(old_mode)

    ############################################
    # Text manipulation
    ############################################

    def substitute_params(self,instruction_string,params):
        p = self._cur_parser()
        return p.substitute_params(instruction_string,params)

    def split_program(self,program_string):
        p = self._cur_parser()
        return p.split_program(program_string)

    def get_text(self,directive_id):
        if directive_id in self.directive_id_to_mode:
            return [self.directive_id_to_mode[directive_id], self._get_raw_text(directive_id)]
        return None

    def _get_raw_text(self, directive_id):
        candidate = self.directive_id_to_stringable_instruction[directive_id]
        candidate = self._ensure_unparsed(candidate)
        self.directive_id_to_stringable_instruction[directive_id] = candidate
        return candidate

    def _ensure_parsed(self, partially_parsed_instruction):
        if isinstance(partially_parsed_instruction, basestring):
            return self._cur_parser().parse_instruction(partially_parsed_instruction)
        elif isinstance(partially_parsed_instruction, dict):
            return self._ensure_parsed_dict(partially_parsed_instruction)
        else:
            raise Exception("Unknown form of partially parsed instruction %s" % partially_parsed_instruction)

    def _ensure_parsed_dict(self, partial_dict):
        def by_key(key, value):
            if key == "instruction":
                return value
            elif key == "expression":
                return self._ensure_parsed_expression(value)
            elif key in ["directive_id", "seed", "inference_timeout"]:
                return self._ensure_parsed_number(value)
            elif key in ["options", "params"]:
                # Do not support partially parsed options or param
                # hashes, since they have too many possible key types
                return value
            elif key in ["symbol", "label"]:
                return value
            elif key == "value":
                # I believe values are a subset of expressions
                return self._ensure_parsed_expression(value)
            else:
                raise Exception("Unknown instruction field %s in %s" % (key, partial_dict))
        return dict([(key, by_key(key, value)) for key, value in partial_dict.iteritems()])

    def _ensure_parsed_expression(self, expr):
        if isinstance(expr, basestring):
            answer = self._cur_parser().parse_expression(expr)
            if isinstance(answer, basestring):
                # Was a symbol; wrap it in a stack dict to prevent it
                # from being processed again.
                return {'type':'symbol', 'value':answer}
            else:
                return answer
        elif isinstance(expr, list):
            return [self._ensure_parsed_expression(e) for e in expr]
        elif isinstance(expr, dict):
            # A literal value as a stack dict.  These are all assumed
            # fully parsed.
            return expr
        elif isinstance(expr, int):
            return v.integer(expr)
        elif isinstance(expr, numbers.Number):
            return v.number(expr)
        elif isinstance(expr, VentureValue):
            # A literal value as a Venture Value
            return expr.asStackDict(None)
        else:
            raise Exception("Unknown partially parsed expression type %s" % expr)

    def _ensure_parsed_number(self, number):
        if isinstance(number, numbers.Number):
            return number
        elif isinstance(number, basestring):
            return self._cur_parser().parse_number(number)
        else:
            raise Exception("Unknown number format %s" % number)

    def _unparse(self, instruction):
        return self._cur_parser().unparse_instruction(instruction)

    def _ensure_unparsed(self, instruction):
        if isinstance(instruction, basestring):
            return instruction
        else:
            # If it didn't come in as a string, do the normalization
            # the parser does before trying to generate a textual
            # representation.  This mitigates possible problems with
            # programmatically generated instructions (as from the
            # assume inference SP). This may lose if the partially
            # parsed instruction has a large string in it.
            return self._unparse(self._ensure_parsed(instruction))

    def character_index_to_expression_index(self, directive_id, character_index):
        p = self._cur_parser()
        expression, offset = self._extract_expression(directive_id)
        return p.character_index_to_expression_index(expression, character_index-offset)

    def expression_index_to_text_index(self, directive_id, expression_index):
        p = self._cur_parser()
        expression, offset = self._extract_expression(directive_id)
        tmp = p.expression_index_to_text_index(expression, expression_index)
        return [x+offset for x in tmp]

    def addr2Source(self, addr):
        """Takes an address and gives the corresponding (unparsed)
        source code and expression index."""

        return self.sivm._resugar(list(addr.last))

    def humanReadable(self, exp=None, did=None, index=None, **kwargs):
        """Take a parsed expression and index and turn it into
        unparsed form with text indeces."""

        p = self._cur_parser()
        exp = p.unparse_expression(exp)
        (start, end) = p.expression_index_to_text_index(exp, index)
        ans = exp[0:start] + "\x1b[31m" + exp[start:end+1] + "\x1b[39;49m" + exp[end+1:]
        return ans, (start, end)

    def draw_subproblem(self, scaffold_dict, type=False):
        # Need to take the "type" argument because
        # MadeRiplMethodInferOutputPSP passes an argument for the type
        # keyword.
        colors = dict(
            red = ("\x1b[31m", "\x1b[39;49m"),
            green = ("\x1b[32m", "\x1b[39;49m"),
            yellow = ("\x1b[33m", "\x1b[39;49m"),
            blue = ("\x1b[34m", "\x1b[39;49m"),
            pink = ("\x1b[35m", "\x1b[39;49m"),
            white = ("\x1b[37m", "\x1b[39;49m"),
            teal = ("\x1b[36m", "\x1b[39;49m"),
            )
        def escape(chunk):
            return re.sub("[[]", "\\[", chunk)
        for (color, (start, stop)) in colors.iteritems():
            pattern = "^" + escape(colors[color][0]) + "([0-9]+)/" + escape(colors[color][1]) + "(.*)$"
            colors[color] = (start, stop, re.compile(pattern))
        def color_app(color):
            def doit(string):
                def do_color(string):
                    return colors[color][0] + string + colors[color][1]
                if string[0] == '(' and string[-1] == ')':
                    return do_color("1/") + do_color("(") + string[1:-1] + do_color(")")
                m = re.match(colors[color][2], string)
                if m is not None:
                    ct = int(m.group(1))
                    return do_color(str(ct+1) + "/") + m.group(2)
                else:
                    return do_color("1/") + string
            return doit
        scaffold = scaffold_dict['value']
        by_did = {}
        def mark(nodes, base_color, only_bottom=False):
            for node in nodes:
                color = color_app(base_color)
                address = node.address.asList()
                stack = self.sivm.trace_address_to_stack(address)
                def add_frame(frame):
                    if frame['did'] not in by_did:
                        by_did[frame['did']] = []
                    by_did[frame['did']].append((frame['index'], color))
                if only_bottom:
                    add_frame(stack[-1])
                else:
                    de_dup = set()
                    for frame in stack:
                        key = (frame['did'], tuple(frame['index']))
                        if key in de_dup: continue
                        de_dup.add(key)
                        add_frame(frame)

        print "The nodes"
        mark(scaffold.getPrincipalNodes(), 'red', only_bottom=True)
        mark(scaffold.drg, 'yellow', only_bottom=True)
        mark(scaffold.absorbing, 'blue', only_bottom=True)
        mark(scaffold.aaa, 'pink', only_bottom=True)
        mark(scaffold.brush, 'green', only_bottom=True)
        for did in sorted(by_did.keys()):
            instr = self.directive_id_to_stringable_instruction[did]
            print self._cur_parser().unparse_instruction(instr, by_did[did])

        print "The stacks"
        by_did = {}
        mark(scaffold.getPrincipalNodes(), 'red', only_bottom=False)
        mark(scaffold.drg, 'yellow', only_bottom=False)
        mark(scaffold.absorbing, 'blue', only_bottom=False)
        mark(scaffold.aaa, 'pink', only_bottom=False)
        mark(scaffold.brush, 'green', only_bottom=False)
        for did in sorted(by_did.keys()):
            instr = self.directive_id_to_stringable_instruction[did]
            print self._cur_parser().unparse_instruction(instr, by_did[did])

    ############################################
    # Directives
    ############################################

    def define(self, name, expression, type=False):
        name = _symbolize(name)
        i = {'instruction':'define', 'symbol':name, 'expression':expression}
        value = self.execute_instruction(i)['value']
        return value if type else u.strip_types(value)

    def assume(self, name, expression, label=None, type=False):
        '''Declare a Venture variable and initialize it by evaluating the
given expression.  Return its value.

The `label` argument, if supplied, can later be passed as an argument
to report, forget, or freeze to refer to this assume directive.

The `type` argument, if supplied and given a true value, causes the
value to be returned as a dict annotating its Venture type.

        '''
        name = _symbolize(name)
        if self.sivm.core_sivm.engine.swapped_model:
            # TODO Properly scope directive labels the models those
            # directives are in.
            # Failing that, this code just suppresses labeling
            # directives in any except the main model.
            if label==None:
                i = {'instruction': 'assume', 'symbol':name, 'expression':expression}
            else:
                raise Exception("TODO Cannot label instructions inside in_model.")
        else:
            if label==None:
                label = name
            else:
                label = _symbolize(label)
            i = {'instruction':'labeled_assume',
                 'symbol':name, 'expression':expression, 'label':label}
        value = self.execute_instruction(i)['value']
        return value if type else u.strip_types(value)

    def predict(self, expression, label=None, type=False):
        if label==None:
            i = {'instruction':'predict', 'expression':expression}
        else:
            label = _symbolize(label)
            i = {'instruction':'labeled_predict', 'expression':expression, 'label':label}
        value = self.execute_instruction(i)['value']
        return value if type else u.strip_types(value)

    def observe(self, expression, value, label=None, type=False):
        if label==None:
            i = {'instruction':'observe', 'expression':expression, 'value':value}
        else:
            label = _symbolize(label)
            i = {'instruction':'labeled_observe', 'expression':expression, 'value':value, 'label':label}
        self.execute_instruction(i)
        return None

    def bulk_observe(self, exp, items, label=None):
        """Observe many evaluations of an expression.

Syntax:
ripl.bulk_observe("<expr>", <iterable>)

Semantics:
Operationally equivalent to::

  for x in iterable:
    ripl.observe("<expr>", x)

but appreciably faster.  See also open considerations and details of
the semantics in `observe_dataset`.

"""
        ret_vals = []
        parsed = self._ensure_parsed_expression(exp)
        for i, val in enumerate(items):
          ret_vals.append(self.observe(parsed,val,label+"_"+str(i) if label is not None else None))
        return ret_vals

    def observe_dataset(self, proc_expression, iterable, label=None):
        """Observe a general dataset.

Syntax:
ripl.observe_dataset("<expr>", <iterable>)

- The expr must evaluate to a (presumably stochastic) Venture
  procedure.  We expect in typical usage expr would just look up a
  recent assume.

- The <iterable> is a Python iterable each of whose elements must be a
  tuple of a list of valid Venture values and a Venture value: ([a], b)

- There is no Venture syntax for this; it is accessible only when
  using Venture as a library.

Semantics:

- As to its effect on the distribution over traces, this is equivalent
  to looping over the contents of the given iterable, calling
  ripl.observe on each element as ripl.observe("(<expr> $tuple[0])",
  tuple[1]). In other words, the first component of each element of
  the iterable gives the arguments to the procedure given by <expr>,
  and the second component gives the value to observe.

- The ripl method returns a list of directive ids, which correspond to
  the individual observes thus generated.

Open issues:

- If the <expr> is itself stochastic, it is unspecified whether we
  notionally evaluate it once per bulk_observe or once per data item.

- This is not the same as directly observing sufficient statistics
  only.

- It is currently not possible to forget the whole bulk_observe at
  once.

- Currently, list_directives will not respect the nesting structure of
  observations implied by bulk_observe.  How can we improve this? Do
  we represent the bulk_observe as one directive? If so, we can hardly
  return a useful representation of the iterable representing the data
  set. If not, we will hardly win anything because list_directives
  will generate all those silly per-datapoint observes (every time
  it's called!)

        """
        ret_vals = []
        parsed = self._ensure_parsed_expression(proc_expression)
        for i, (args, val) in enumerate(iterable):
          expr = [parsed] + [v.quote(a) for a in args]
          ret_vals.append(self.observe(expr,val,label+"_"+str(i) if label is not None else None))
        return ret_vals

    ############################################
    # Core
    ############################################

    def configure(self, options=None):
        if options is None: options = {}
        i = {'instruction':'configure', 'options':options}
        return self.execute_instruction(i)['options']

    def get_seed(self):
        return self.configure()['seed']

    def set_seed(self, seed):
        self.configure({'seed': seed})
        return None

    def get_inference_timeout(self):
        return self.configure()['inference_timeout']

    def set_inference_timeout(self, inference_timeout):
        self.configure({'inference_timeout': inference_timeout})
        return None

    def forget(self, label_or_did, type=False):
        if isinstance(label_or_did,int):
            i = {'instruction':'forget', 'directive_id':label_or_did}
            # if asked to forget prelude instruction, decrement _n_prelude
            if label_or_did <= self._n_prelude:
                self._n_prelude -= 1
        else:
            # assume that prelude instructions don't have labels
            i = {'instruction':'labeled_forget',
                 'label':_symbolize(label_or_did)}
        self.execute_instruction(i)
        return None

    def freeze(self, label_or_did, type=False):
        if isinstance(label_or_did,int):
            i = {'instruction':'freeze', 'directive_id':label_or_did}
        else:
            i = {'instruction':'labeled_freeze',
                 'label':_symbolize(label_or_did)}
        self.execute_instruction(i)
        return None

    def report(self, label_or_did, type=False):
        if isinstance(label_or_did,int):
            i = {'instruction':'report', 'directive_id':label_or_did}
        else:
            i = {'instruction':'labeled_report',
                 'label':v.symbol(label_or_did)}
        value = self.execute_instruction(i)['value']
        return value if type else u.strip_types(value)

    def defaultInferProgram(self, program):
        try: # Check for being a string that represents an int
            program = int(program)
        except: pass
        if program is None:
            if self.mode == 'church_prime':
                return "(rejection default all 1)"
            if self.mode == 'venture_script':
                return "rejection(default, all, 1)"
        elif isinstance(program, int):
            if self.mode == 'church_prime':
                return "(mh default one %d)" % program
            if self.mode == 'venture_script':
                return "mh(default, one, %d)" % program
        else:
            return program

    def infer(self, params=None, type=False, suppress_pausing_continous_inference=False):
        # The suppress_pausing_continous_inference flag is used by the
        # thread doing the continuous inference.
        o = self.execute_instruction({'instruction':'infer', 'expression': self.defaultInferProgram(params)}, suppress_pausing_continous_inference=suppress_pausing_continous_inference)
        value = o["value"]
        return value if type else u.strip_types(value)

    def clear(self):
        self.execute_instruction({'instruction':'clear'})
        # if you clear the ripl, you lose all the prelude commands
        # TODO: change this behavior
        self._n_prelude = 0
        return None

    def rollback(self):
        self.execute_instruction({'instruction':'rollback'})
        return None

    def list_directives(self, type=False, include_prelude = False, instructions = []):
        with self.sivm._pause_continuous_inference():
            directives = self.execute_instruction({'instruction':'list_directives'})['directives']
            # modified to add value to each directive
            # FIXME: is this correct behavior?
            for directive in directives:
                inst = { 'instruction':'report',
                         'directive_id':directive['directive_id'],
                         }
                value = self.execute_instruction(inst)['value']
                directive['value'] = value if type else u.strip_types(value)
            # if not requested to include the prelude, exclude those directives
            if hasattr(self, '_n_prelude') and (not include_prelude):
                directives = directives[self._n_prelude:]
            if len(instructions) > 0:
                directives = [d for d in directives if d['instruction'] in instructions]
            return directives

    def print_directives(self, *instructions, **kwargs):
        for directive in self.list_directives(instructions = instructions, **kwargs):
            dir_id = int(directive['directive_id'])
            dir_val = str(directive['value'])
            dir_type = directive['instruction']
            dir_text = self._get_raw_text(dir_id)

            if dir_type == "assume":
                print "%d: %s:\t%s" % (dir_id, dir_text, dir_val)
            elif dir_type == "observe":
                print "%d: %s" % (dir_id, dir_text)
            elif dir_type == "predict":
                print "%d: %s:\t %s" % (dir_id, dir_text, dir_val)
            else:
                assert False, "Unknown directive type found: %s" % str(directive)

    def get_directive(self, label_or_did):
        if isinstance(label_or_did,int):
            i = {'instruction':'get_directive', 'directive_id':label_or_did}
        else:
            i = {'instruction':'labeled_get_directive',
                 'label':v.symbol(label_or_did)}
        return self.execute_instruction(i)['directive']

    def force(self, expression, value):
        i = {'instruction':'force', 'expression':expression, 'value':value}
        self.execute_instruction(i)
        return None

    def sample(self, expression, type=False):
        i = {'instruction':'sample', 'expression':expression}
        value = self.execute_instruction(i)['value']
        return value if type else u.strip_types(value)

    def sample_all(self, expression, type=False):
        expression = self._ensure_parsed_expression(expression)
        value = self.sivm.core_sivm.engine.sample_all(expression)
        return value if type else u.strip_types(value)

    def continuous_inference_status(self):
        return self.execute_instruction({'instruction':'continuous_inference_status'})

    def start_continuous_inference(self, program=None):
        self.execute_instruction({'instruction':'start_continuous_inference', 'expression': self.defaultInferProgram(program)})
        return None

    def stop_continuous_inference(self):
        self.execute_instruction({'instruction':'stop_continuous_inference'})
        return None

    def get_current_exception(self):
        return self.execute_instruction({'instruction':'get_current_exception'})['exception']

    def get_state(self):
        return self.execute_instruction({'instruction':'get_state'})['state']

    def reinit_inference_problem(self, num_particles=None):
        # TODO Adapt to renumbering of directives by the engine (or
        # change the engine not to do that)
        # TODO Go through the actual stack?
        self.sivm.core_sivm.engine.reinit_inference_problem(num_particles)

    def get_global_logscore(self):
        return self.execute_instruction({'instruction':'get_global_logscore'})['logscore']

    def register_foreign_sp(self, name, sp):
        # TODO Remember this somehow?  Is it storable for copies and
        # rebuilds of the ripl, etc?
        self.sivm.core_sivm.engine.register_foreign_sp(name, sp)

    def bind_foreign_sp(self, name, sp):
        self.register_foreign_sp(name, sp)
        self.sivm.core_sivm.engine.import_foreign(name)

    def bind_foreign_inference_sp(self, name, sp):
        self.sivm.core_sivm.engine.bind_foreign_inference_sp(name, sp)

    def bind_callback(self, name, callback):
        self.sivm.core_sivm.engine.bind_callback(name, callback)

    def bind_methods_as_callbacks(self, obj, prefix=""):
        """Bind every public method of the given object as a callback of the same name."""
        for name in (name for name in dir(obj) if not name.startswith("_")):
            self.bind_callback(prefix + name, getattr(obj, name))

    ############################################
    # Serialization
    ############################################

    def save(self, fname):
        extra = {}
        extra['directive_id_to_stringable_instruction'] = self.directive_id_to_stringable_instruction
        extra['directive_id_to_mode'] = self.directive_id_to_mode
        return self.sivm.save(fname, extra)

    def load(self, fname):
        extra = self.sivm.load(fname)
        self.directive_id_to_stringable_instruction = extra['directive_id_to_stringable_instruction']
        self.directive_id_to_mode = extra['directive_id_to_mode']

    ############################################
    # Profiler methods (stubs)
    ############################################

    def profiler_configure(self, options=None):
        if options is None: options = {}
        i = {'instruction': 'profiler_configure', 'options': options}
        return self.execute_instruction(i)['options']

    def profiler_enable(self):
        self.profiler_configure({'profiler_enabled': True})
        return None

    def profiler_disable(self):
        self.profiler_configure({'profiler_enabled': False})
        return None

    def profiler_clear(self):
        self.random_choices = []
        self.address_to_acceptance_rate = {}
        self.address_to_proposal_time = {}
        return None

    # insert a random choice into the profiler
    def profiler_make_random_choice(self):
        import random
        address = random.randrange(1 << 16)
        trials = random.randrange(1, 1000)
        successes = random.randint(0, trials)
        proposal_time = trials * random.random()

        self.random_choices.append(address)
        self.address_to_acceptance_rate[address] = (trials, successes)
        self.address_to_proposal_time[address] = proposal_time

        return address

    def profiler_list_random_choices(self):
        return self.random_choices

    def profiler_address_to_source_code_location(self,address):
        return address

    def profiler_get_acceptance_rate(self,address):
        return self.address_to_acceptance_rate[address]

    def profiler_get_proposal_time(self,address):
        return self.address_to_proposal_time[address]

    ############################################
    # Hacky profiling support since the above is ill understood
    ############################################

    def profile_data(self):
        rows = self.sivm.core_sivm.engine.profile_data()

        def replace(d, name, f):
            if name in d:
                d[name] = f(d[name])

        def resugar(addr):
            stuff = self.addr2Source(addr)
            return (stuff['did'], tuple(stuff['index']))

        def getaddr((did, index)):
            from venture.exception import underline
            exp = self.sivm._get_exp(did) #pylint: disable=protected-access
            text, indyces = self.humanReadable(exp, did, index)
            return text + '\n' + underline(indyces)

        def sort_as(initial, final, xs):
            'Given xs in order "initial", re-sort in order "final"'
            ix = np.argsort([final.index(x) for x in initial])
            return np.array(xs)[ix].tolist()

        for row in rows:
            initial_order = map(resugar, row['principal'])
            for name in ['principal', 'absorbing', 'aaa']:
                replace(row, name, lambda addrs: frozenset(map(resugar, addrs)))
            # reorder the human-readable addresses, current and proposed values
            final_order = list(row['principal'])
            row['address'] = [getaddr(x) for x in row['principal']]
            for name in ['current', 'proposed']:
                row[name] = sort_as(initial_order, final_order, row[name])

        from pandas import DataFrame
        return DataFrame.from_records(rows)

    _parsed_prelude = None

    ############################################
    # Library
    ############################################
    def load_prelude(self):
        '''
        Load the library of Venture helper functions
        '''
        if Ripl._parsed_prelude is not None:
            self.execute_parsed_program(*Ripl._parsed_prelude)
            # Keep track of the number of directives in the prelude. Only
            # works if the ripl is cleared immediately before loading the
            # prelude, but that's the implicit assumption in the
            # _n_prelude concept anyway.
            self._n_prelude += len(self.list_directives(include_prelude = True))
        elif self.mode == 'church_prime':
            prelude_path = path.join(path.dirname(__file__), PRELUDE_FILE)
            with open(prelude_path) as f:
                Ripl._parsed_prelude = self.parse_program(f.read())
            self.load_prelude()

    def load_plugin(self, name, *args, **kwargs):
        m = load_library(name)
        if hasattr(m, "__venture_start__"):
            return m.__venture_start__(self, *args, **kwargs)

    ############################################
    # Private methods
    ############################################

    def _cur_parser(self):
        return self.parsers[self.mode]

    def _extract_expression(self,directive_id):
        text = self._get_raw_text(directive_id)
        mode = self.directive_id_to_mode[directive_id]
        p = self.parsers[mode]
        args, arg_ranges = p.split_instruction(text)
        return args['expression'], arg_ranges['expression'][0]

def load_library(name):
    import imp
    pathname = name
    if name.endswith('.py'):
        name = name[0 : len(name) - len('.py')]
    with open(pathname, 'rb') as f:
        return imp.load_source(name, pathname, f)

    # XXX Why don't we use imp.find_module and imp.load_module?
    # Desiderata:
    # - Be able to import things relative to either the working
    #   directory or the location of the .vnt file.
    # - Permit those to import relative to themselves, if possible.
    #
    # None of the methods below achieve both of these things.  The
    # latter, and the implement option, permit a loaded plugin to load
    # other relative modules by sys.path hacking.

    # exec("import %s as plugin_mod" % name)
    # return plugin_mod

    # import importlib
    # return importlib.import_module(name)

    # return __import__("import %s" % name)

    # (file, pathname, description) = imp.find_module(name, ["."] + sys.path)
    # print (file, pathname, description)
    # return imp.load_module(name, file, pathname, description)

def _symbolize(thing):
    if isinstance(thing, basestring):
        return v.symbol(thing)
    else:
        return thing # Assume it's already the proper stack dict
