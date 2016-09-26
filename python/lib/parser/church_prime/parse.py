# Copyright (c) 2014, 2015, 2016 MIT Probabilistic Computing Project.
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

from venture.parser import ast
from venture.parser.church_prime import grammar
from venture.parser.church_prime import scan

def locquoted(located_quoter, located_value, f):
    (_vstart, vend) = located_value.loc
    (start, _end) = located_quoter.loc
    assert start < _vstart
    return ast.Located([start, vend], f(located_value))

def expression_evaluation_instruction(e):
    return { 'instruction': ast.update_value(e, 'evaluate'), 'expression': e }

def delocust(l):
    # XXX Why do we bother with tuples in the first place?
    if isinstance(l, dict) and sorted(l.keys()) == ['loc', 'value']:
        return delocust(l['value'])
    elif ast.isloc(l):
        return delocust(l.value)
    elif isinstance(l, list) or isinstance(l, tuple):
        return [delocust(v) for v in l]
    elif isinstance(l, dict):
        return dict((k, delocust(v)) for k, v in l.iteritems())
    else:
        return l

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
    '<-':       '<-',
}

class Semantics(object):
    def __init__(self):
        self.answer = None

    def accept(self):
        assert self.answer is not None
    def parse_failed(self):
        assert self.answer is None
        raise VentureException('parse', 'Syntax error!')
    def syntax_error(self, (_number, located)):
        # XXX Should not raise here -- should accumulate errors and
        # report them all at the end.
        #
        # XXX Should adapt lemonade to support passing a message, and
        # make the generated parser say which tokens (and, ideally,
        # nonterminals) it was expecting instead.
        text = located.value
        (start, end) = located.loc
        raise VentureException('parse', ('Syntax error at %s' % (repr(text),)),
            text_index=[start, end])

    # Venture start symbol: store result in self.answer, return none.
    def p_venture_empty(self):
        self.answer = []
    def p_venture_i(self, insts):
        self.answer = insts

    # instructions: Return list of instructions.
    def p_instructions_one(self, inst):
        return [inst]
    def p_instructions_many(self, insts, inst):
        insts.append(inst)
        return insts

    # instruction: Return located { 'instruction': 'foo', ... }.
    def p_instruction_labelled(self, l, open, d, close):
        label = ast.map_value(val.symbol, l)
        if d['instruction'].value == 'evaluate':
            # The grammar only permits expressions that are calls to
            # the 'assume', 'observe', or 'predict' macros to be
            # labeled with syntactic sugar.
            locexp = d['expression']
            exp = locexp.value
            new_exp = exp + [label]
            new_locexp = ast.Located(locexp.loc, new_exp)
            new_d = expression_evaluation_instruction(new_locexp)
            return ast.locmerge(l, close, new_d)
        else:
            d['label'] = label
            d['instruction'] = ast.map_value(lambda i: 'labeled_' + i, d['instruction'])
            return ast.locmerge(l, close, d)
    def p_instruction_unlabelled(self, open, d, close):
        return ast.locmerge(open, close, d)
    def p_instruction_command(self, open, c, close):
        return ast.locmerge(open, close, c)
    def p_instruction_expression(self, e):
        inst = expression_evaluation_instruction(e)
        return ast.update_value(e, inst)
    def p_instruction_laberror(self, d):
        return 'error'
    def p_instruction_labdirerror(self):
        return 'error'
    def p_instruction_error(self):
        return 'error'

    # directive: Return { 'instruction': located(..., 'foo'), ... }.
    def p_directive_define(self, k, n, e):
        return { 'instruction': ast.update_value(k, 'define'),
                 'symbol': ast.map_value(val.symbol, n), 'expression': e }
    def p_directive_assume(self, k, n, e):
        # Fun fact.  This manipulation (and the similar treatment of
        # observe and predict, here and in the VentureScript parser)
        # breaks an invariant that parsing used to satisfy.  To wit,
        # once upon a time it was the case that the string picked out
        # by the location tags of every node in a parse tree was
        # guaranteed to re-parse to an equal node.  This cannot be the
        # case now, because the 'expr' node constructed here is not
        # parsed from the string, but synthesized based on knowing
        # that its constituents appear in an 'assume' directive.
        expr = [ast.update_value(k, val.symbol('assume')),
                ast.map_value(val.symbol, n),
                e]
        return expression_evaluation_instruction(ast.loclist(expr))
    def p_directive_assume_values(self, k, nl, e):
        expr = [ast.update_value(k, val.symbol('assume_values')),
                nl,
                e]
        return expression_evaluation_instruction(ast.loclist(expr))
    def p_directive_observe(self, k, e, e1):
        expr = [ast.update_value(k, val.symbol('observe')), e, e1]
        return expression_evaluation_instruction(ast.loclist(expr))
    def p_directive_predict(self, k, e):
        expr = [ast.update_value(k, val.symbol('predict')), e]
        return expression_evaluation_instruction(ast.loclist(expr))

    # command: Return { 'instruction': located(..., 'foo'), ... }.
    def p_command_infer(self, k, e):
        return { 'instruction': ast.update_value(k, 'infer'), 'expression': e }
    def p_command_load(self, k, pathname):
        return { 'instruction': ast.update_value(k, 'load'),
                 'file': pathname }

    # expression: Return located expression.
    def p_expression_symbol(self, name):
        return ast.map_value(val.symbol, name)
    def p_expression_operator(self, op):
        assert op.value in operators
        return ast.map_value(lambda op: val.symbol(operators[op]), op)
    def p_expression_literal(self, value):
        return value
    def p_expression_quote(self, quote, e):
        return locquoted(quote, e, val.quote)
    def p_expression_qquote(self, qquote, e):
        return locquoted(qquote, e, val.quasiquote)
    def p_expression_unquote(self, unquote, e):
        return locquoted(unquote, e, val.unquote)
    def p_expression_comb0(self, open, close):
        return ast.locmerge(open, close, [])
    def p_expression_comb1(self, open, op, args, close):
        return ast.locmerge(open, close, [op] + args)
    def p_expression_comb_error(self, open, op, args, close):
        return 'error'

    # arguments: Return list of expressions.
    def p_arguments_none(self):
        return []
    def p_arguments_some(self, args, e):
        args.append(e)
        return args
    def p_arguments_some_kw(self, args, name, colon, e):
        args.append(e)
        return args # The colons are for fake keyword syntax, see Issue #445.
    def p_arguments_kw_error(self, args, name, colon):
        return 'error'

    # namelist: return a located list of names
    def p_namelist_nl(self, open, ns, close):
        return ast.locmerge(open, close, ns)

    # names: return list of located symbols
    def p_names_none(self):
        return []
    def p_names_some(self, ns, n):
        ns.append(ast.map_value(val.symbol, n))
        return ns

    # literal: Return located `val'.
    def p_literal_true(self, t):
        return ast.map_value(val.boolean, ast.update_value(t, True))
    def p_literal_false(self, f):
        return ast.map_value(val.boolean, ast.update_value(f, False))
    def p_literal_integer(self, v):
        return ast.map_value(val.number, v)
    def p_literal_real(self, v):
        return ast.map_value(val.number, v)
    def p_literal_string(self, v):
        return ast.map_value(val.string, v)
    def p_literal_json(self, type, open, value, close):
        t = type.value
        start, end = type.loc
        if t == 'boolean':
            raise VentureException('parse', ('JSON not allowed for %s' % (t,)),
                text_index=[start, end])
        return ast.locmerge(type, close, { 'type': t, 'value': value })

    # json: Return json object.
    def p_json_string(self, v):                 return v.value
    def p_json_integer(self, v):                return v.value
    def p_json_real(self, v):                   return v.value
    def p_json_list(self, l):                   return l
    def p_json_dict(self, d):                   return d

    # json_list: Return list.
    def p_json_list_l(self, b):                 return b
    def p_json_list_empty(self):                return []
    def p_json_list_nonempty(self, ts):         return ts
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
    def p_json_dict_entry_e(self, key, value):  return (key.value, value)
    def p_json_dict_entry_error(self, value):   return ('error', value)

def parse_church_prime(f, context, languages=None):
    if languages:
        import warnings
        warnings.warn('Church Prime supports no sublanguages: %r' %
            (languages,))
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
    assert semantics.answer is not None
    return semantics.answer

def parse_church_prime_string(string, languages=None):
    try:
        return parse_church_prime(StringIO.StringIO(string), '(string)',
            languages)
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


def string_complete_p(string, languages=None):
    if languages:
        import warnings
        warnings.warn('Church Prime supports no sublanguages: %r' %
            (languages,))
    scanner = scan.Scanner(StringIO.StringIO(string), '(string)')
    semantics = Semantics()
    parser = grammar.Parser(semantics)
    while True:
        token = scanner.read()
        if token[0] == -1:      # scan error
            return True
        else:
            if token[0] == 0:   # EOF
                try:
                    parser.feed(token)
                    # If the EOF parses, then we had a complete string
                    return True
                except VentureException:
                    # Parse was not complete
                    return False
            else:
                parser.feed(token)

def parse_instructions(string, languages=None):
    return map(ast.as_legacy_dict, parse_church_prime_string(string, languages))

def parse_instruction(string, languages=None):
    ls = parse_instructions(string, languages)
    if len(ls) != 1:
        msg = 'Expected %s to parse as a single instruction, got %s' % (string, ls)
        raise VentureException('parse', msg)
    return ls[0]

def parse_expression(string, languages=None):
    inst = parse_instruction(string, languages)['value']
    if inst['instruction']['value'] != 'evaluate':
        raise VentureException('parse', 'Expected an expression')
    return inst['expression']

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
    elif v['type'] == 'string':
        assert isinstance(v['value'], basestring)
        return quote_string(v['value'])
    elif v['type'] == 'array_unboxed':
        # first problem: the JSON representation for this isn't one-to-one,
        # because it doesn't include a way to specify subtype.
        # second: the value might be a numpy array, which JSON doesn't like.
        # solution: convert to lite's VentureValue, unbox, convert back.
        # XXX is there a better way?
        from venture.lite.value import VentureValue, VentureArray
        v = VentureValue.fromStackDict(v)
        v = VentureArray(v.getArray())
        v = v.asStackDict()
        return '%s<%s>' % (v['type'], json.dumps(v['value']))
    else:
        return '%s<%s>' % (v['type'], json.dumps(v['value']))

escapes = {
    '/':    '/',
    '\"':   '\"',
    '\\':   '\\',
    '\b':   'b',            # Backspace
    '\f':   'f',            # Form feed
    '\n':   'n',            # Line feed
    '\r':   'r',            # Carriage return
    '\t':   't',            # Horizontal tab
}

def quote_string(s):
    out = StringIO.StringIO()
    out.write('"')
    for ch in s:
        if ch in escapes:
            out.write('\\')
            out.write(escapes[ch])
        else:
            out.write(ch)
    out.write('"')
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

    def parse_instructions(self, string, languages=None):
        '''Parse STRING as a list of instructions.'''
        l = parse_instructions(string, languages)
        return delocust(l)

    def parse_instruction(self, string, languages=None):
        '''Parse STRING as a single instruction.'''
        l = parse_instruction(string, languages)
        return delocust(l)

    def parse_locexpression(self, string, languages=None):
        '''Parse STRING as an expression, and include location records.'''
        return parse_expression(string, languages)

    def parse_expression(self, string, languages=None):
        '''Parse STRING as an expression.'''
        return delocust(parse_expression(string, languages))

    def unparse_expression(self, expression):
        '''Unparse EXPRESSION into a string.'''
        if isinstance(expression, dict):
            if expression["type"] == "array":
                # Because combinations actually parse as arrays too,
                # and I want the canonical form to be that.
                return self.unparse_expression(expression["value"])
            else: # Leaf
                return value_to_string(expression)
        elif isinstance(expression, basestring):
            # XXX This is due to &@!#^&$@!^$&@#!^%&*.
            return expression
        elif isinstance(expression, list):
            terms = (self.unparse_expression(e) for e in expression)
            return '(' + ' '.join(terms) + ')'
        else:
            raise TypeError('Invalid expression: %s of type %s' % (repr(expression),type(expression)))

    def unparse_integer(self, integer):
        return str(integer)
    def unparse_string(self, string):
        return quote_string(string)
    def unparse_symbol(self, symbol):
        assert isinstance(symbol, dict)
        assert 'type' in symbol
        assert symbol['type'] == 'symbol'
        return tagged_value_to_string(symbol)
    def unparse_symbol_quoted(self, symbol):
        return "'" + self.unparse_symbol(symbol)
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
        'forget': [('directive_id', unparse_integer)],
        'labeled_forget': [('label', unparse_symbol)],
        'freeze': [('directive_id', unparse_integer)],
        'labeled_freeze': [('label', unparse_symbol)],
        'report': [('directive_id', unparse_integer)],
        'labeled_report': [('label', unparse_symbol_quoted)],
        'infer': [('expression', unparse_expression)],
        'clear': [],
        'force': [('expression', unparse_expression), ('value', unparse_value)],
        'sample': [('expression', unparse_expression)],
        'continuous_inference_status': [],
        'start_continuous_inference': [('expression', unparse_expression)],
        'stop_continuous_inference': [],
        'load': [('file', unparse_string)],
    }
    def unparse_instruction(self, instruction, expr_markers=None):
        '''Unparse INSTRUCTION into a string.'''
        # XXX Urgh.  Whattakludge!
        i = instruction['instruction']
        if i == 'evaluate':
            return self.unparse_expression_and_mark_up(
                instruction['expression'], expr_markers)
        unparsers = self.unparsers[i]
        if i in ['forget', 'labeled_forget', 'freeze', 'labeled_freeze',
                 'report', 'labeled_report', 'clear',
                 'force', 'sample', 'continuous_inference_status',
                 'start_continuous_inference', 'stop_continuous_inference',
        ]:
            open_char = '('
            close_char = ')'
        else:
            open_char = '['
            close_char = ']'
        chunks = []
        if 'label' in instruction and 'label' not in (k for k,_u in unparsers):
            chunks.append(instruction['label']['value'])
            chunks.append(': ')
        chunks.append(open_char)
        if i[0 : len('labeled_')] == 'labeled_':
            chunks.append(i[len('labeled_'):])
        else:
            chunks.append(i)
        for key, unparser in unparsers:
            chunks.append(' ')
            if key == 'expression': # Urk
                chunks.append(self.unparse_expression_and_mark_up(
                    instruction[key], expr_markers))
            else:
                chunks.append(unparser(self, instruction[key]))
        chunks.append(close_char)
        return ''.join(chunks)

    # XXX ???
    def parse_number(self, string):
        '''Parse STRING as an integer or real number.'''
        return float(string) if '.' in string else int(string)

    # XXX ???
    def split_instruction(self, string, languages=None):
        '''Split STRING into a dict of instruction operands.

        Return a two-element list containing
        [0] a dict mapping operand keys to substrings of STRING; and
        [1] a dict mapping operand keys to [start, end] positions.
        '''
        l = parse_instruction(string, languages)
        locs = dict((k, v['loc']) for k, v in l['value'].iteritems())
        # XXX + 1?
        strings = dict((k, string[loc[0] : loc[1] + 1]) for k, loc in
            locs.iteritems())
        # XXX Sort???
        sortlocs = dict((k, list(sorted(loc))) for k, loc in locs.iteritems())
        # XXX List???
        return [strings, sortlocs]

    def expression_index_to_text_index(self, string, index, languages=None):
        '''Return position of expression in STRING indexed by INDEX.

        - STRING is a string of an expression.
        - INDEX is a list of indices into successively nested
          subexpressions.

        Return [start, end] position of the last nested subexpression.
        '''
        l = parse_expression(string, languages)
        return self._expression_index_to_text_index_in_parsed_expression(l, index, string)

    def _expression_index_to_text_index_in_parsed_expression(self, l, index, string):
        for i in range(len(index)):
            if index[i] < 0 or len(l['value']) <= index[i]:
                raise ValueError('Index out of range: %s in %s' %
                    (index, repr(string)))
            l = l['value'][index[i]]
        return l['loc']

    def expression_index_to_text_index_in_instruction(self, string, index,
            languages=None):
        '''Return position of expression in STRING indexed by INDEX.

        - STRING is a string of an instruction that has a unique expression.
        - INDEX is a list of indices into successively nested
          subexpressions.

        Return [start, end] position of the last nested subexpression.
        '''
        inst = parse_instruction(string, languages)
        l = inst['value']['expression']
        return self._expression_index_to_text_index_in_parsed_expression(l, index, string)

    def unparse_expression_and_mark_up(self, exp, places=None):
        '''Return a string representing the given EXP with markings at the given PLACES.

        - EXP is a parsed expression
        - PLACES is an association list from index lists to markers
          - each key is a list of indices into successively nested
            subexpressions
          - each marker is a string->string function
        '''
        if places is not None:
            marker_trie = Trie.from_list(places)
        else:
            marker_trie = None
        return self._unparse_expression_and_mark_up_with_trie(exp, marker_trie)

    def _unparse_expression_and_mark_up_with_trie(self, exp, markers):
        if markers is None:
            return self.unparse_expression(exp)
        def unparse_leaf(leaf, markers):
            ans = leaf
            for f in markers.tops():
                ans = f(ans)
            return ans
        if isinstance(exp, dict):
            if exp["type"] == "array":
                # Because combinations actually parse as arrays too,
                # and I want the canonical form to be that.
                return self._unparse_expression_and_mark_up_with_trie(exp["value"], markers)
            else: # Leaf
                if markers.has_children():
                    print "Warning: index mismatch detected: looking for children of %s." % value_to_string(exp)
                return unparse_leaf(value_to_string(exp), markers)
        elif isinstance(exp, basestring):
            # XXX This is due to &@!#^&$@!^$&@#!^%&*.
            if markers.has_children():
                print "Warning: index mismatch detected: looking for children of string-exp %s." % exp
            return unparse_leaf(exp, markers)
        elif isinstance(exp, list):
            terms = (self._unparse_expression_and_mark_up_with_trie(e, markers.get(i))
                     for (i, e) in enumerate(exp))
            return unparse_leaf('(' + ' '.join(terms) + ')', markers)
        else:
            raise TypeError('Invalid expression: %s of type %s' % (repr(exp),type(exp)))

class Trie(object):
    '''A compact representation of an association with sequence keys.

    A trie node is the set of values whose remaining key suffix is the
    empty list, together with a map from next key elements to Trie
    nodes representing the key suffixes remaining after stripping
    those elements.

    In Haskell:
      data Trie k v = Trie (Maybe v) (Map k (Trie k v))
    which is isomorphic (at least for finite key lists) to
      Map [k] v
    but more compact and supports more efficient subset queries by
    prefix.

    For my application, the values of the trie are actually lists of
    all the values having that key.

    '''

    def __init__(self, here_list, later_nodes):
        self.here_list = here_list
        self.later_nodes = later_nodes

    def has_top(self):
        return self.here_list

    def top(self):
        return self.here_list[0]

    def tops(self):
        return self.here_list

    def has_children(self):
        return self.later_nodes

    def get(self, k):
        if k in self.later_nodes:
            return self.later_nodes[k]
        else:
            return None

    def insert(self, ks, v):
        if not ks: # Empty list
            self.here_list.append(v)
        else:
            self._ensure(ks[0]).insert(ks[1:], v)

    def _ensure(self, k):
        if k not in self.later_nodes:
            self.later_nodes[k] = Trie.empty()
        return self.later_nodes[k]

    @staticmethod
    def empty():
        return Trie([], {})

    @staticmethod
    def from_list(keyed_items):
        answer = Trie.empty()
        for (ks, v) in keyed_items:
            answer.insert(ks, v)
        return answer
