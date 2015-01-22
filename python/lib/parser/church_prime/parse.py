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
import json

from venture.exception import VentureException
import venture.value.dicts as val

from venture.parser.church_prime import grammar
from venture.parser.church_prime import scan

def tokval((value, _start, _end)):
    return value

def located(loc, value):
    # XXX Use a namedtuple, not a dict.
    return { 'loc': loc, 'value': value }

def locmap(l, f):
    return { 'loc': l['loc'], 'value': f(l['value']) }

def loctoken((value, start, end)):
    return located([start, end], value)

def loctoken1((_value, start, end), value):
    return located([start, end], value)

def locbracket((_ovalue, ostart, oend), (_cvalue, cstart, cend), value):
    assert ostart <= oend
    assert oend < cstart
    assert cstart <= cend
    return located([ostart, cend], value)

def delocust(l):
    # XXX Why do we bother with tuples in the first place?
    if isinstance(l['value'], list) or isinstance(l['value'], tuple):
        return [delocust(v) for v in l['value']]
    else:
        return l['value']

operators = {
    '+':        'add',
    '-':        'sub',
    '*':        'mul',
    '/':        'div',
    '<':        'lt',
    '>':        'gt',
    '<=':       'lte',
    '>=':       'gte',
    '=':        'eq',
    '!=':       'neq',
}

class Semantics(object):
    def __init__(self):
        self.answer = None

    def accept(self):
        assert self.answer is not None
    def parse_failed(self):
        assert self.answer is None
        raise VentureException('parse', 'Syntax error!')
    def syntax_error(self, (_number, (text, start, end))):
        # XXX Should not raise here -- should accumulate errors and
        # report them all at the end.
        #
        # XXX Should adapt lemonade to support passing a message, and
        # make the generated parser say which tokens (and, ideally,
        # nonterminals) it was expecting instead.
        raise VentureException('parse', ('Syntax error at %s' % (repr(text,))),
            text_index=[start, end])

    # Venture start symbol: store result in self.answer, return none.
    def p_venture_empty(self):
        self.answer = ('instructions', [])
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
        d['instruction'] = locmap(d['instruction'], lambda i: 'labeled_' + i)
        return locbracket(l, close, d)
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

    # directive: Return { 'instruction': located(..., 'foo'), ... }.
    def p_directive_define(self, k, n, e):
        return { 'instruction': loctoken1(k, 'define'),
                 'symbol': locmap(loctoken(n), val.symbol), 'expression': e }
    def p_directive_assume(self, k, n, e):
        return { 'instruction': loctoken1(k, 'assume'),
                 'symbol': locmap(loctoken(n), val.symbol), 'expression': e }
    def p_directive_observe(self, k, e, v):
        return { 'instruction': loctoken1(k, 'observe'),
                 'expression': e, 'value': v }
    def p_directive_predict(self, k, e):
        return { 'instruction': loctoken1(k, 'predict'), 'expression': e }

    # command: Return { 'instruction': located(..., 'foo'), ... }.
    def p_command_configure(self, k, options):
        return { 'instruction': loctoken1(k, 'configure'), 'options': options }
    def p_command_forget(self, k, dr):
        i = 'labeled_forget' if dr[0] == 'label' else 'forget'
        return { 'instruction': loctoken1(k, i), dr[0]: dr[1] }
    def p_command_report(self, k, dr):
        i = 'labeled_report' if dr[0] == 'label' else 'report'
        return { 'instruction': loctoken1(k, i), dr[0]: dr[1] }
    def p_command_infer(self, k, e):
        return { 'instruction': loctoken1(k, 'infer'), 'expression': e }
    def p_command_clear(self, k):
        return { 'instruction': loctoken1(k, 'clear') }
    def p_command_rollback(self, k):
        return { 'instruction': loctoken1(k, 'rollback') }
    def p_command_list_directives(self, k):
        return { 'instruction': loctoken1(k, 'list_directives') }
    def p_command_get_directive(self, k, dr):
        i = 'labeled_get_directive' if dr[0] == 'label' else 'get_directive'
        return { 'instruction': loctoken1(k, i), dr[0]: dr[1] }
    def p_command_force(self, k, e, v):
        return { 'instruction': loctoken1(k, 'force'), 'expression': e,
                 'value': v }
    def p_command_sample(self, k, e):
        return { 'instruction': loctoken1(k, 'sample'), 'expression': e }
    def p_command_continuous_inference_status(self, k):
        return { 'instruction': loctoken1(k, 'continuous_inference_status') }
    def p_command_start_continuous_inference(self, k, e):
        return { 'instruction': loctoken1(k, 'start_continuous_inference'),
                 'expression': e }
    def p_command_stop_continuous_inference(self, k):
        return { 'instruction': loctoken1(k, 'stop_continuous_inference') }
    def p_command_get_current_exception(self, k):
        return { 'instruction': loctoken1(k, 'get_current_exception') }
    def p_command_get_state(self, k):
        return { 'instruction': loctoken1(k, 'get_state') }
    def p_command_get_logscore(self, k, dr):
        i = 'labeled_get_logscore' if dr[0] == 'label' else 'get_logscore'
        return { 'instruction': loctoken1(k, i), dr[0]: dr[1] }
    def p_command_get_global_logscore(self, k):
        return { 'instruction': loctoken1(k, 'get_global_logscore') }
    def p_command_profiler_configure(self, k, options):
        return { 'instruction': loctoken1(k, 'profiler_configure'),
                 'options': options }
    def p_command_profiler_clear(self, k):
        return { 'instruction': loctoken1(k, 'profiler_clear') }
    def p_command_list_random(self, k):
        return { 'instruction': loctoken1(k, 'profiler_list_random_choices') }
    def p_command_load(self, k, pathname):
        return { 'instruction': loctoken1(k, 'load'),
                 'file': loctoken(pathname) }

    # directive_ref: Return (reftype, located value) tuple.
    def p_directive_ref_numbered(self, number):
        return ('directive_id', loctoken(number))
    def p_directive_ref_labelled(self, label):
        return ('label', loctoken(label))

    # expression: Return located expression.
    def p_expression_symbol(self, name):
        return locmap(loctoken(name), val.symbol)
    def p_expression_operator(self, op):
        assert op[0] in operators
        return locmap(loctoken(op), lambda op: val.symbol(operators[op]))
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
        t, start, end = type
        if t == 'number' or t == 'boolean':
            raise VentureException('parse', ('JSON not allowed for %s' % (t,)),
                text_index=[start, end])
        return locbracket(type, close, { 'type': t, 'value': value })

    # json: Return json object.
    def p_json_string(self, v):                 return tokval(v)
    def p_json_integer(self, v):                return tokval(v)
    def p_json_real(self, v):                   return tokval(v)
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
    def p_json_dict_entry_e(self, key, value):  return (tokval(key), value)
    def p_json_dict_entry_error(self, value):   return ('error', value)

def parse_church_prime(f, context):
    scanner = scan.Scanner(f, context)
    semantics = Semantics()
    parser = grammar.Parser(semantics)
    while True:
        token = scanner.read()
        if token[0] == -1:      # error
            semantics.syntax_error(token)
        else:
            parser.feed(token)
        if token[0] == 0:       # EOF
            break
    return semantics.answer

def parse_church_prime_string(string):
    try:
        return parse_church_prime(StringIO.StringIO(string), '(string)')
    except VentureException as e:
        assert 'instruction_string' not in e.data
        if 'text_index' in e.data:
            [start, end] = e.data['text_index']
            lstart = string.rfind('\n', 0, start)
            if lstart == -1:
                lstart = 0
            else:
                lstart += 1
            lend = string.find('\n', end + 1)
            if lend == -1:
                lend = len(string)
            e.data['instruction_string'] = string[lstart : lend]
            e.data['text_index'] = [start - lstart, end - lstart]
        raise e

def parse_instructions(string):
    t, ls = parse_church_prime_string(string)
    if t != 'instructions':
        raise VentureException('parse', 'Expected instructions')
    return ls

def parse_instruction(string):
    ls = parse_instructions(string)
    if len(ls) != 1:
        raise VentureException('parse', 'Expected a single instruction')
    return ls[0]

def parse_expression(string):
    t, l = parse_church_prime_string(string)
    if t != 'expression':
        raise VentureException('parse', 'Expected an expression')
    return l

def value_to_string(v):
    if isinstance(v, dict):
        return tagged_value_to_string(v)
    elif isinstance(v, bool):
        return 'true' if v else 'false'
    elif isinstance(v, basestring):
        return v
    else:
        raise TypeError('Invalid Venture value: %s' % (repr(v),))

def tagged_value_to_string(v):
    assert 'type' in v
    assert 'value' in v
    if v['type'] == 'boolean':
        assert v['value'] in set([True, False])
        return 'true' if v['value'] else 'false'
    elif v['type'] == 'number':
        assert isinstance(v['value'], int) or isinstance(v['value'], float)
        return str(v['value'])
    elif v['type'] == 'symbol':
        assert isinstance(v['value'], basestring)
        return v['value']
    else:
        return '%s<%s>' % (v['type'], json.dumps(v['value']))

# XXX Ugh, whattakludge.  If we can get rid of substitute_params, we
# can get rid of this.
def value_or_number_to_string(v):
    if isinstance(v, int) or isinstance(v, float):
        return str(v)
    else:
        return value_to_string(v)

formatters = {
    's': str,
    'v': value_or_number_to_string,
    'j': json.dumps,
}

def substitute_params(string, params):
    if isinstance(params, tuple) or isinstance(params, list):
        return substitute_params_indexed(string, params)
    elif isinstance(params, dict):
        return substitute_params_named(string, params)
    else:
        raise TypeError('Invalid parameter set: %s' % (params,))

def substitute_params_indexed(string, params):
    out = StringIO.StringIO()
    i = 0
    n = 0
    while i < len(string):
        j = string.find('%', i)
        if j == -1:
            j = len(string)     # Silly indexing convention.
        if i < j:
            out.write(buffer(string, i, j - i))
        if j == len(string):
            break
        j += 1
        if j == len(string):
            raise ValueError('Dangling escape: %s' % (repr(string),))
        d = string[j]
        if d == '%':
            out.write('%')
        else:
            if d not in formatters:
                raise ValueError('Unknown formatting directive: %s' % (d,))
            if n == len(params):
                raise ValueError('Not enough parameters %d: %s' %
                    (n, repr(string)))
            out.write(formatters[d](params[n]))
            n += 1
        i = j + 1
    return out.getvalue()

def substitute_params_named(string, params):
    out = StringIO.StringIO()
    i = 0
    while i < len(string):
        j = string.find('%', i)
        if j == -1:
            j = len(string)     # Silly indexing convention.
        if i < j:
            out.write(buffer(string, i, j - i))
        if j == len(string):
            break
        j += 1
        if j == len(string):
            raise ValueError('Dangling escape: %s' % (repr(string),))
        if string[j] == '%':
            out.write('%')
        elif string[j] == '(':
            k = string.find(')', j + 1)
            if k == -1 or k + 1 == len(string):
                raise ValueError('Dangling escape: %s' % (repr(string),))
            key = string[j + 1 : k]
            if key not in params:
                raise ValueError('Missing parameter: %s' % (key,))
            out.write(formatters[string[k + 1]](params[key]))
        else:
            raise ValueError('Invalid formatting directive: %%%s' %
                (string[j],))
    return out.getvalue()

the_parser = None

class ChurchPrimeParser(object):
    '''Legacy interface to Church' parser.'''

    @staticmethod
    def instance():
        '''Return the global Church' parser instance.'''
        global the_parser
        if the_parser is None:
            the_parser = ChurchPrimeParser()
        return the_parser

    # XXX Doesn't really belong here.
    def substitute_params(self, string, params):
        '''Return STRING with %-directives formatted using PARAMS.'''
        return substitute_params(string, params)

    # XXX Make the tests pass, nobody else calls this.
    def get_instruction_string(self, i):
        d = {
            'observe': '[ observe %(expression)s %(value)v ]',
            'infer': '[ infer %(expression)s ]',
        }
        return d[i]

    def parse_instruction(self, string):
        '''Parse STRING as a single instruction.'''
        l = parse_instruction(string)
        return dict((k, delocust(v)) for k, v in l['value'].iteritems())

    def parse_locexpression(self, string):
        '''Parse STRING as an expression, and include location records.'''
        return parse_expression(string)

    def parse_expression(self, string):
        '''Parse STRING as an expression.'''
        return delocust(parse_expression(string))

    def unparse_expression(self, expression):
        '''Unparse EXPRESSION into a string.'''
        if isinstance(expression, dict):        # Leaf.
            return value_to_string(expression)
        elif isinstance(expression, basestring):
            # XXX This is due to &@!#^&$@!^$&@#!^%&*.
            return expression
        elif isinstance(expression, list):
            terms = (self.unparse_expression(e) for e in expression)
            return '(' + ' '.join(terms) + ')'
        else:
            raise TypeError('Invalid expression: %s' % (repr(expression),))

    def unparse_integer(self, integer):
        return str(integer)
    def unparse_symbol(self, symbol):
        assert isinstance(symbol, dict)
        assert 'type' in symbol
        assert symbol['type'] == 'symbol'
        return tagged_value_to_string(symbol)
    def unparse_value(self, value):
        return value_to_string(value)
    def unparse_json(self, obj):
        return json.dumps(obj)

    # XXX The one useful property the old parser had is that this
    # table was written once, in one place, for the parser and
    # unparser.  Well, actually, twice -- once for church prime and
    # once for venture script, with slight differences...
    unparsers = {
        'define': [('symbol', unparse_symbol), ('expression', unparse_expression)],
        'labeled_define': [('symbol', unparse_symbol), ('expression', unparse_expression)],
        'assume': [('symbol', unparse_symbol), ('expression', unparse_expression)],
        'labeled_assume': [('symbol', unparse_symbol), ('expression', unparse_expression)],
        'observe': [('expression', unparse_expression), ('value', unparse_value)],
        'labeled_observe': [('expression', unparse_expression), ('value', unparse_value)],
        'predict': [('expression', unparse_expression)],
        'labeled_predict': [('expression', unparse_expression)],
        'configure': [('options', unparse_json)],
        'forget': [('directive_id', unparse_integer)],
        'labeled_forget': [('label', unparse_symbol)],
        'report': [('directive_id', unparse_integer)],
        'labeled_report': [('label', unparse_symbol)],
        'infer': [('expression', unparse_expression)],
        'clear': [],
        'rollback': [],
        'list_directives': [],
        'get_directive': [('directive_id', unparse_integer)],
        'labeled_get_directive': [('label', unparse_symbol)],
        'force': [('expression', unparse_expression), ('value', unparse_value)],
        'sample': [('expression', unparse_expression)],
        'continuous_inference_status': [],
        'start_continuous_inference': [('expression', unparse_expression)],
        'stop_continuous_inference': [],
        'get_current_exception': [],
        'get_state': [],
        'get_logscore': [('directive_id', unparse_integer)],
        'labeled_get_logscore': [('label', unparse_symbol)],
        'profiler_configure': [('options', unparse_json)],
        'profiler_clear': [],
        'profiler_list_random': [], # XXX Urk, extra keyword.
        'load': [('file', unparse_json)],
    }
    def unparse_instruction(self, instruction):
        '''Unparse INSTRUCTION into a string.'''
        # XXX Urgh.  Whattakludge!
        i = instruction['instruction']
        unparsers = self.unparsers[i]
        chunks = []
        if 'label' in instruction and 'label' not in (k for k,_u in unparsers):
            chunks.append(instruction['label'])
            chunks.append(': ')
        chunks.append('[')
        if i[0 : len('labeled_')] == 'labeled_':
            chunks.append(i[len('labeled_'):])
        else:
            chunks.append(i)
        for key, unparser in unparsers:
            chunks.append(' ')
            chunks.append(unparser(self, instruction[key]))
        chunks.append(']')
        return ''.join(chunks)

    # XXX ???
    def parse_number(self, string):
        '''Parse STRING as an integer or real number.'''
        return float(string) if '.' in string else int(string)

    # XXX ???
    def split_program(self, string):
        '''Split STRING into a sequence of instructions.

        Return a two-element list containing
        [0] a list of substrings, one for each instruction; and
        [1] a list of [start, end] positions of each instruction in STRING.
        '''
        ls = parse_instructions(string)
        locs = [l['loc'] for l in ls]
        # XXX + 1?
        strings = [string[loc[0] : loc[1] + 1] for loc in locs]
        # XXX Sort??
        sortlocs = [list(sorted(loc)) for loc in locs]
        # XXX List???
        return [strings, sortlocs]

    # XXX ???
    def split_instruction(self, string):
        '''Split STRING into a dict of instruction operands.

        Return a two-element list containing
        [0] a dict mapping operand keys to substrings of STRING; and
        [1] a dict mapping operand keys to [start, end] positions.
        '''
        l = parse_instruction(string)
        locs = dict((k, v['loc']) for k, v in l['value'].iteritems())
        # XXX + 1?
        strings = dict((k, string[loc[0] : loc[1] + 1]) for k, loc in
            locs.iteritems())
        # XXX Sort???
        sortlocs = dict((k, list(sorted(loc))) for k, loc in locs.iteritems())
        # XXX List???
        return [strings, sortlocs]

    # XXX Make the tests pass, nobody else calls this.
    def character_index_to_expression_index(self, _string, index):
        '''Return bogus data to make tests pass.  Nobody cares!'''
        return [[], [0], [], None, None, [2], [2,0]][index]

    def expression_index_to_text_index(self, string, index):
        '''Return position of expression in STRING indexed by INDEX.

        - STRING is a string of an expression.
        - INDEX is a list of indices into successively nested
          subexpressions.

        Return [start, end] position of the last nested subexpression.
        '''
        l = parse_expression(string)
        for i in range(len(index)):
            if index[i] < 0 or len(l['value']) <= index[i]:
                raise ValueError('Index out of range: %s in %s' %
                    (index, repr(string)))
            l = l['value'][index[i]]
        return l['loc']
