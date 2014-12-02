# Copyright (c) 2014, MIT Probabilistic Computing Project.
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

# Venture parser (`Church prime', Lisp-style notation).

import StringIO
import collections

import venture.value.dicts as val

from venture.parser.church_prime import grammar
from venture.parser.church_prime import scan

def located(loc, value):
    # XXX Use a namedtuple, not a dict.
    return { 'loc': loc, 'value': value }

def locmap(l, f):
    return { 'loc': l['loc'], 'value': f(l['value']) }

def loc1(l, v):
    return located(l['loc'], v)

def loc2(a, b, value):
    [start_a, end_a] = a['loc']
    [start_b, end_b] = b['loc']
    loc = [min(start_a, start_b), max(end_a, end_b)]
    return located(loc, value)

def locmerge(a, b, f):
    return loc2(a, b, f(a['value'], b['value']))

def loctoken((value, start, end)):
    return located([start, end], value)

def loctoken1((_value, start, end), value):
    return located([start, end], value)

def locbracket((ovalue, ostart, oend), (cvalue, cstart, cend), value):
    return located([ostart, cend], value)

def locunit(l):
    return loc1(l, [l])

def locappend(l, x):
    l1 = l['value']
    l1.append(x)
    return loc2(l, x, l1)

class Semantics(object):
    def __init__(self):
        self.answer = None

    def accept(self):
        assert self.answer is not None
    def parse_failed(self):
        assert self.answer is None
    def syntax_error(self, token):
        print 'Syntax error: %s' % (token,)

    # Venture start symbol: store result in self.answer, return none.
    def p_venture_empty(self):
        self.answer = []
    def p_venture_i(self, insts):
        self.answer = ('instructions', insts)
    def p_venture_e(self, exp):
        self.answer = ('expression', exp)

    # instructions: Return list of instructions.
    def p_instructions_one(self, inst):
        return [inst]
    def p_instructions_many(self, insts, inst):
        insts.append(inst)
        return insts

    # instruction: Return located { 'instruction': 'foo', ... }.
    def p_instruction_labelled(self, l, open, d, close):
        d['label'] = loctoken(l)
        return loc2(loctoken(l), loctoken(close), d)
    def p_instruction_unlabelled(self, open, d, close):
        return locbracket(open, close, d)
    def p_instruction_command(self, open, c, close):
        return locbracket(open, close, c)
    def p_instruction_laberror(self, d):
        return 'error'
    def p_instruction_labdirerror(self):
        return 'error'
    def p_instruction_error(self):
        return 'error'

    # directive: Return { 'instruction': 'foo', ... }.
    def p_directive_assume(self, n, e):
        return { 'instruction': 'assume', 'symbol': n, 'expression': e }
    def p_directive_observe(self, e, v):
        return { 'instruction': 'observe', 'expression': e, 'value': v }
    def p_directive_predict(self, e):
        return { 'instruction': 'predict', 'expression': e }

    # command: Return { 'instruction': 'foo', ... }.
    def p_command_configure(self, options):
        return { 'instruction': 'configure', 'options': options }
    def p_command_forget(self, dr):
        return { 'instruction': 'forget', dr[0]: dr[1] }
    def p_command_report(self, dr):
        return { 'instruction': 'report', dr[0]: dr[1] }
    def p_command_infer(self, e):
        return { 'instruction': 'infer', 'expression': e }
    def p_command_clear(self):
        return { 'instruction': 'clear' }
    def p_command_rollback(self):
        return { 'instruction': 'rollback' }
    def p_command_list_directives(self):
        return { 'instruction': 'list_directives' }
    def p_command_get_directive(self, dr):
        return { 'instruction': 'get_directive', dr[0]: dr[1] }
    def p_command_force(self, e, v):
        return { 'instruction': 'force', 'expression': e, 'value': v }
    def p_command_sample(self, e):
        return { 'instruction': 'sample', 'expression': e }
    def p_command_continuous_inference_status(self):
        return { 'instruction': 'continuous_inference_status' }
    def p_command_stop_continuous_inference(self):
        return { 'instruction': 'stop_continuous_inference' }
    def p_command_get_current_exception(self):
        return { 'instruction': 'get_current_exception' }
    def p_command_get_state(self):
        return { 'instruction': 'get_state' }
    def p_command_get_logscore(self, dr):
        return { 'instruction': 'get_logscore', dr[0]: dr[1] }
    def p_command_get_global_logscore(self):
        return { 'instruction': 'get_global_logscore' }
    def p_command_profiler_configure(self, options):
        return { 'instruction': 'profiler_configure', 'options': options }
    def p_command_profiler_clear(self):
        return { 'instruction': 'profiler_clear' }
    def p_command_list_random(self):
        return { 'instruction': 'profiler_list_random_choices' }
    def p_command_load(self, pathname):
        return { 'instruction': 'load', 'file': pathname }

    # directive_ref: Return (reftype, located value) tuple.
    def p_directive_ref_numbered(self, number):
        return ('directive_id', loctoken(number))
    def p_directive_ref_labelled(self, label):
        return ('label', loctoken(label))

    # top_expression: Return located expression.
    def p_top_expression_literal(self, value):
        return value
    def p_top_expression_combination(self, open, es, close):
        return locbracket(open, close, es or [])
    def p_top_expression_comb_error(self, open, es, close):
        return 'error'

    # expression: Return located expression.
    def p_expression_symbol(self, name):
        return locmap(loctoken(name), val.symbol)
    def p_expression_literal(self, value):
        return value
    def p_expression_combination(self, open, es, close):
        return locbracket(open, close, es or [])
    def p_expression_comb_error(self, open, es, close):
        return 'error'

    # expressions: Return list of expressions, or None.
    def p_expressions_none(self):
        return []
    def p_expressions_some(self, es, e):
        es.append(e)
        return es

    # literal: Return located `val'.
    def p_literal_true(self, t):
        return locmap(loctoken1(t, True), val.boolean)
    def p_literal_false(self, f):
        return locmap(loctoken1(f, False), val.boolean)
    def p_literal_integer(self, v):
        return locmap(loctoken(v), val.number)
    def p_literal_real(self, v):
        return locmap(loctoken(v), val.number)
    def p_literal_json(self, type, open, value, close):
        type, _start, _end = type
        if type == 'number' or type == 'boolean':
            raise SyntaxError('Write numbers and booleans without JSON!')
        return loc2(loctoken(open), loctoken(close),
            { 'type': type, 'value': value })

    # json: Return json object.
    def p_json_string(self, v):                 return v
    def p_json_integer(self, v):                return v
    def p_json_real(self, v):                   return v
    def p_json_list(self, l):                   return l
    def p_json_dict(self, d):                   return d

    # json_list: Return list.
    def p_json_list_l(self, b):                 return b
    def p_json_list_body_none(self):            return []
    def p_json_list_body_some(self, ts):        return ts
    def p_json_list_terms_one(self, t):         return [t]
    def p_json_list_terms_many(self, ts, t):    ts.append(t); return ts
    def p_json_list_terms_error(self, t):       return ['error']

    # json_dict: Return dict.
    def p_json_dict_empty(self):                return {}
    def p_json_dict_nonempty(self, es):         return es
    def p_json_dict_error(self, es):            return ['error']

    # json_dict_entries: Return dict.
    def p_json_dict_entries_one(self, e):       return { e[0]: e[1] }
    # XXX Check for duplicates.
    def p_json_dict_entries_many(self, es, e):  es[e[0]] = e[1]; return es
    def p_json_dict_entries_error(self, e):     return { 'error': 'error' }

    # json_dict_entry: Return (key, value) tuple.
    def p_json_dict_entry_e(self, key, value):  return (key, value)
    def p_json_dict_entry_error(self, value):   return ('error', value)

def parse_venture(f):
    scanner = scan.Scanner(f, '(string)')
    semantics = Semantics()
    parser = grammar.Parser(semantics)
    while True:
        token = scanner.read()
        if token[0] is None:
            parser.feed((0, None))
            break
        parser.feed(token)
    return semantics.answer
