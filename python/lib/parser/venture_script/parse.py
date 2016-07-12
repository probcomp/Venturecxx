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

# Venture parser (`VentureScript', JavaScript-style notation).

import StringIO
import json

from venture.exception import VentureException
import venture.value.dicts as val

from venture.parser.venture_script import grammar
from venture.parser.venture_script import scan

def tokval((value, _start, _end)):
    return value

def isloc(obj):
    return isinstance(obj, dict) and sorted(obj.keys()) == ['loc', 'value']

def located(loc, value):
    # XXX Use a namedtuple, not a dict.
    return {'loc': loc, 'value': value}

def locval(lv, v):
    return {'loc': lv['loc'], 'value': v}

def locmap(l, f):
    return {'loc': l['loc'], 'value': f(l['value'])}

def locmerge(lv0, lv1, v):
    start0, end0 = lv0['loc']
    start1, end1 = lv1['loc']
    assert start0 < end1
    return {'loc': [start0, end1], 'value': v}

def loctoken((value, start, end)):
    return located([start, end], value)

def loctoken1((_value, start, end), value):
    return located([start, end], value)

def locquoted((_value, start, _end), located_value, f):
    (_vstart, vend) = located_value['loc']
    assert start < _vstart
    return located([start, vend], f(located_value))

def locbracket((_ovalue, ostart, oend), (_cvalue, cstart, cend), value):
    assert ostart <= oend
    assert oend < cstart
    assert cstart <= cend
    return located([ostart, cend], value)

def loclist(items):
    assert len(items) >= 1
    (start, _) = items[0]['loc']
    (_, end) = items[-1]['loc']
    return located([start, end], items)

def expression_evaluation_instruction(e):
    return { 'instruction': locmap(e, lambda _: 'evaluate'), 'expression': e }

def delocust(l):
    # XXX Why do we bother with tuples in the first place?
    if isinstance(l['value'], list) or isinstance(l['value'], tuple):
        return [delocust(v) for v in l['value']]
    else:
        return l['value']

def adjlocust(l, o):
    start, end = l['loc']
    v = l['value']
    if isinstance(v, list) or isinstance(v, tuple):
        v = [adjlocust(u, o) for u in v]
    return {'loc': [start + o, end + o], 'value': v}

operators = {
    '+':        'add',
    '-':        'sub',
    '*':        'mul',
    '/':        'div',
    '**':       'pow',
    '<':        'lt',
    '>':        'gt',
    '<=':       'lte',
    '>=':       'gte',
    '==':       'eq',  # XXX Church' uses = for eq, VScript uses = for def.
    '!=':       'neq',
    '&&':       'and',
    '||':       'or',
    '<-':       '<-',
}

class Semantics(object):
    def __init__(self):
        self.answer = None

    def accept(self):
        assert self.answer is not None
    def parse_failed(self):
        assert self.answer is None
        raise VentureException('text_parse', 'Syntax error!')
    def syntax_error(self, (number, (text, start, end))):
        # XXX Should not raise here -- should accumulate errors and
        # report them all at the end.
        #
        # XXX Should adapt lemonade to support passing a message, and
        # make the generated parser say which tokens (and, ideally,
        # nonterminals) it was expecting instead.
        raise VentureException('text_parse',
            ('Syntax error at %s (token %d)' % (repr(text), number)),
            text_index=[start, end])

    # Venture start symbol: store result in self.answer, return none.
    def p_venture_top(self, insts):
        for i in insts:
            assert isloc(i)
        self.answer = insts

    # instructions: Return list of located instructions.
    def p_instructions_none(self):
        return []
    def p_instructions_some(self, insts, inst):
        if inst is not None:
            assert isloc(inst)
            insts.append(inst)
        return insts

    # instruction_opt: Return located instruction or None.
    def p_instruction_opt_none(self):
        return None
    def p_instruction_opt_some(self, inst):
        assert isloc(inst)
        return inst

    # instruction: Return located {'instruction': 'foo', ...}.
    def p_instruction_command(self, c):
        assert isloc(c)
        return c
    def p_instruction_statement(self, e):
        i = locval(e, 'evaluate')
        return locval(e, {'instruction': i, 'expression': e})

    # labelled: Return located expression.
    def p_labelled_directive(self, l, d):
        label = locmap(loctoken(l), val.symbol)
        exp = d['value']
        new_exp = exp + [label]
        new_d = locmerge(label, d, new_exp)
        return new_d
    def p_labelled_directive_prog(self, dol, lab_exp, d):
        label = locmerge(loctoken(dol), lab_exp, val.unquote(lab_exp))
        exp = d['value']
        new_exp = exp + [label]
        new_d = locmerge(label, d, new_exp)
        return new_d

    # directive: Return located expression.
    def p_directive_assume(self, k, n, eq, e):
        assert isloc(e)
        i = loctoken1(k, val.symbol('assume'))
        s = locmap(loctoken(n), val.symbol)
        app = [i, s, e]
        return locmerge(i, e, app)
    def p_directive_assume_prog(self, k, dol, sym_exp, eq, e):
        assert isloc(e)
        assert isloc(sym_exp)
        i = loctoken1(k, val.symbol('assume'))
        app = [i, locmerge(loctoken(dol), sym_exp, val.unquote(sym_exp)), e]
        return locmerge(i, e, app)
    def p_directive_observe(self, k, e, eq, e1):
        assert isloc(e)
        assert isloc(e1)
        i = loctoken1(k, val.symbol('observe'))
        app = [i, e, e1]
        return locmerge(i, e1, app)
    def p_directive_predict(self, k, e):
        assert isloc(e)
        i = loctoken1(k, val.symbol('predict'))
        app = [i, e]
        return locmerge(i, e, app)

    # command: Return located { 'instruction': located(..., 'foo'), ... }.
    def p_command_define(self, k, n, eq, e):
        assert isloc(e)
        i = loctoken1(k, 'define')
        s = locmap(loctoken(n), val.symbol)
        return locmerge(i, e, {'instruction': i, 'symbol': s, 'expression': e})
    def p_command_infer(self, k, e):
        assert isloc(e)
        i = loctoken1(k, 'infer')
        return locmerge(i, e, {'instruction': i, 'expression': e})
    def p_command_load(self, k, pathname):
        i = loctoken1(k, 'load')
        p = loctoken(pathname)
        return locmerge(i, p, {'instruction': i, 'file': p})

    # body: Return located expression.
    def p_body_do(self, ss, semi, e):
        assert isloc(ss)
        if e is None:
            e = loctoken1(semi, val.symbol('pass'))
        assert isloc(e)
        do = locmerge(ss, e, val.symbol('do'))
        return locmerge(ss, e, [do] + ss['value'] + [e])
    def p_body_exp(self, e):
        assert isloc(e)
        return e

    # statements: Return located list of located bindings.
    def p_statements_one(self, s):
        assert isloc(s)
        return locval(s, [s])
    def p_statements_many(self, ss, semi, s):
        assert isloc(s)
        assert isloc(s)
        ss['value'].append(s)
        return locmerge(ss, s, ss['value'])

    def p_statement_let(self, l, n, eq, e):
        assert isloc(e)
        let = loctoken1(l, val.symbol('let'))
        n = locmap(loctoken(n), val.symbol)
        return locmerge(let, e, [let, n, e])
    def p_statement_assign(self, n, eq, e):
        assert isloc(e)
        let = loctoken1(eq, val.symbol('let'))
        n = locmap(loctoken(n), val.symbol)
        return locmerge(n, e, [let, n, e])
    def p_statement_letrec(self, l, n, eq, e):
        assert isloc(e)
        let = loctoken1(l, val.symbol('letrec'))
        n = locmap(loctoken(n), val.symbol)
        return locmerge(let, e, [let, n, e])
    def p_statement_mutrec(self, l, n, eq, e):
        assert isloc(e)
        let = loctoken1(l, val.symbol('mutrec'))
        n = locmap(loctoken(n), val.symbol)
        return locmerge(let, e, [let, n, e])
    def p_statement_letvalues(self, l, po, names, pc, eq, e):
        assert isloc(e)
        assert all(map(isloc, names))
        let = loctoken1(l, val.symbol('let_values'))
        names = locbracket(po, pc, names)
        return locmerge(let, e, [let, names, e])
    def p_statement_labelled(self, d):
        assert isloc(d)
        return d
    def p_statement_none(self, e):
        assert isloc(e)
        return e

    # expression_opt: Return located expression or None.
    def p_expression_opt_none(self):
        return None
    def p_expression_opt_some(self, e):
        assert isloc(e)
        return e

    def _p_binop(self, l, op, r):
        assert isloc(l)
        assert isloc(r)
        assert tokval(op) in operators
        app = [locmap(loctoken1(op, operators[tokval(op)]), val.symbol), l, r]
        return locmerge(l, r, app)
    def _p_exp(self, e):
        assert isloc(e)
        return e

    # expression: Return located expression.
    p_expression_top = _p_exp
    def p_do_bind_bind(self, n, op, e):
        assert isloc(e)
        n = loctoken(n)
        # XXX Yes, this remains infix, for the macro expander to handle...
        # XXX Convert <~ to <- for the macro expander's sake
        return locmerge(n, e, [n, locmap(loctoken(op), lambda s: val.symbol("<-")), e])
    def p_do_bind_labelled(self, n, op, l):
        assert isloc(l)
        n = loctoken(n)
        # XXX Yes, this remains infix, for the macro expander to handle...
        # XXX Convert <~ to <- for the macro expander's sake
        return locmerge(n, l, [n, locmap(loctoken(op), lambda s: val.symbol("<-")), l])
    def p_action_directive(self, d):
        assert isloc(d)
        return d
    def p_action_force(self, k, e1, eq, e2):
        assert isloc(e1)
        assert isloc(e2)
        i = loctoken1(k, val.symbol('force'))
        app = [i, e1, e2]
        return locmerge(i, e2, app)
    def p_action_sample(self, k, e):
        assert isloc(e)
        i = loctoken1(k, val.symbol('sample'))
        app = [i, e]
        return locmerge(i, e, app)
    def p_arrow_one(self, param, op, body):
        assert isloc(body)
        param = locmap(loctoken(param), val.symbol)
        return locmerge(param, body, [
            locmap(loctoken1(op, 'lambda'), val.symbol),
            locval(param, [param]),
            body,
        ])
    def p_arrow_tuple(self, po, params, pc, op, body):
        assert isloc(body)
        return locmerge(loctoken(po), body, [
            locmap(loctoken1(op, 'lambda'), val.symbol),
            locbracket(po, pc, params),
            body,
        ])
    p_do_bind_none = _p_exp
    p_action_none = _p_exp
    p_arrow_none = _p_exp
    p_boolean_or_or = _p_binop
    p_boolean_or_none = _p_exp
    p_boolean_and_and = _p_binop
    p_boolean_and_none = _p_exp
    p_equality_eq = _p_binop
    p_equality_neq = _p_binop
    p_equality_none = _p_exp
    p_comparison_lt = _p_binop
    p_comparison_le = _p_binop
    p_comparison_ge = _p_binop
    p_comparison_gt = _p_binop
    p_comparison_none = _p_exp
    p_additive_add = _p_binop
    p_additive_sub = _p_binop
    p_additive_none = _p_exp
    p_multiplicative_mul = _p_binop
    p_multiplicative_div = _p_binop
    p_multiplicative_none = _p_exp
    p_exponential_pow = _p_binop
    p_exponential_none = _p_exp

    def p_applicative_app(self, fn, o, args, c):
        assert isloc(fn)
        for arg in args:
            assert isloc(arg)
        return locmerge(fn, loctoken(c), [fn] + args)
    def p_applicative_lookup(self, a, o, index, c):
        assert isloc(a)
        assert isloc(index)
        lookup = loctoken1(o, val.sym('lookup'))
        return locmerge(a, loctoken(c), [lookup, a, index])
    def p_applicative_none(self, e):
        assert isloc(e)
        return e

    # arglist, args: Return list of located expressions.
    def p_arglist_none(self):           return []
    def p_arglist_some(self, args):     return args
    def p_args_one(self, arg):          return [arg]
    def p_args_many(self, args, arg):   args.append(arg); return args
    def p_tagged_none(self, e):         return e
    def p_tagged_kw(self, name, colon, e): return e

    def p_primary_paren(self, o, es, c):
        assert isinstance(es, list) and all(map(isloc, es))
        if len(es) == 1:
            [e] = es
            return locbracket(o, c, e['value'])
        else:
            construction = [locmap(loctoken1(o, 'values_list'), val.symbol)] + es
            return locbracket(o, c, construction)
    def p_primary_brace(self, o, e, c):
        assert isloc(e)
        return locbracket(o, c, e['value'])
    def p_primary_proc(self, k, po, params, pc, bo, body, bc):
        assert isloc(body)
        return locbracket(k, bc, [
            locmap(loctoken1(k, 'lambda'), val.symbol),
            locbracket(po, pc, params),
            body,
        ])
    def p_primary_if(self, k, po, p, pc, co, c, cc, ke, ao, a, ac):
        assert isloc(p)
        assert isloc(c)
        assert isloc(a)
        return locbracket(k, ac,
            [locmap(loctoken1(k, 'if'), val.symbol), p, c, a])
    def p_primary_qquote(self, o, b, c):
        return locbracket(o, c, val.quasiquote(b))
    def p_primary_unquote(self, op, e):
        op = loctoken(op)
        return locmerge(op, e,
            val.quote(locmerge(op, e, val.unquote(e))))
    def p_primary_array(self, o, a, c):
        assert isinstance(a, list)
        construction = [locmap(loctoken1(o, 'array'), val.symbol)] + a
        return locbracket(o, c, construction)
    def p_primary_literal(self, l):
        assert isloc(l)
        return l
    def p_primary_symbol(self, s):
        return locmap(loctoken(s), val.symbol)
    def p_primary_language(self, ll):
        l, start, _end = ll
        assert isloc(l), '%r' % (l,)
        l_ = adjlocust(l, start)
        return l_

    # paramlist, params: Return list of located symbols.
    def p_paramlist_none(self):                 return []
    def p_paramlist_some(self, params):         return params
    def p_params_one(self, param):
        return [locmap(loctoken(param), val.symbol)]
    def p_params_many(self, params, c, param):
        params.append(locmap(loctoken(param), val.symbol))
        return params

    # arraybody, arrayelts: Return list of located expressions.
    def p_arraybody_none(self):                 return []
    def p_arraybody_some(self, es):             return es
    def p_arrayelts_one(self, e):               return [e]
    def p_arrayelts_many(self, es, c, e):       es.append(e); return es

    # literal: Return located `val'.
    def p_literal_true(self, t):
        return locmap(loctoken1(t, True), val.boolean)
    def p_literal_false(self, f):
        return locmap(loctoken1(f, False), val.boolean)
    def p_literal_integer(self, v):
        return locmap(loctoken(v), val.number)
    def p_literal_real(self, v):
        return locmap(loctoken(v), val.number)
    def p_literal_string(self, v):
        return locmap(loctoken(v), val.string)
    def p_literal_json(self, t, v, c):
        t0, start, end = t
        assert t0[-1] == '<'
        t0 = t0[:-1]
        if t0 == 'boolean':
            # XXX Accumulate parse error.
            raise VentureException('text_parse',
                ('JSON not allowed for %s' % (t0,)),
                text_index=[start, end])
        return locbracket(t, c, {'type': t0, 'value': v})

    # json: Return json object.
    def p_json_string(self, v):                 return tokval(v)
    def p_json_integer(self, v):                return tokval(v)
    def p_json_real(self, v):                   return tokval(v)
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
    def p_json_dict_entry_e(self, key, value):  return (tokval(key), value)
    def p_json_dict_entry_error(self, value):   return ('error', value)

def parse(f, context, languages=None):
    scanner = scan.Scanner(f, context, languages)
    semantics = Semantics()
    parser = grammar.Parser(semantics)
    while True:
        token = scanner.read()
        if token[0] == -1:      # error
            semantics.syntax_error(token)
        else:
            if token[0] == 0:   # EOF
                # Implicit ; at EOF.
                semi = (';', scanner.cur_pos, scanner.cur_pos)
                parser.feed((grammar.T_SEMI, semi))
            parser.feed(token)
        if token[0] == 0:       # EOF
            break
    assert isinstance(semantics.answer, list)
    for i in semantics.answer:
        assert isloc(i)
    return semantics.answer

def parse_string(string, languages=None):
    try:
        return parse(StringIO.StringIO(string), '(string)', languages)
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
    # XXX This protocol won't work very well with embedded languages.
    scanner = scan.Scanner(StringIO.StringIO(string), '(string)', languages)
    semantics = Semantics()
    parser = grammar.Parser(semantics)
    while True:
        token = scanner.read()
        if token[0] == -1:      # scan error
            return True
        else:
            if token[0] == 0:   # EOF
                # Implicit ; at EOF.
                semi = (';', scanner.cur_pos, scanner.cur_pos)
                try:
                    parser.feed((grammar.T_SEMI, semi))
                    # If the semi parses, then we had a complete string
                    return True
                except VentureException:
                    # Parse was not complete
                    return False
            else:
                parser.feed(token)

def parse_instructions(string, languages=None):
    return parse_string(string, languages)

def parse_instruction(string, languages=None):
    ls = parse_instructions(string, languages)
    if len(ls) != 1:
        raise VentureException('text_parse', 'Expected a single instruction')
    return ls[0]

def parse_expression(string, languages=None):
    inst = parse_instruction(string, languages)['value']
    if not inst['instruction']['value'] == 'evaluate':
        raise VentureException('text_parse', 'Expected an expression')
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

class VentureScriptParser(object):
    '''Legacy interface to VentureScript parser.'''

    @staticmethod
    def instance():
        '''Return the global VentureScript parser instance.'''
        global the_parser
        if the_parser is None:
            the_parser = VentureScriptParser()
        return the_parser

    # XXX Rather than having a global VentureScriptParser instance
    # with methods that take an optional embedded language set, we
    # should perhaps pass the embedded language set as an instance
    # variable of VentureScriptParser.

    def parse_instruction(self, string, languages=None):
        '''Parse STRING as a single instruction.'''
        l = parse_instruction(string, languages)
        return dict((k, delocust(v)) for k, v in l['value'].iteritems())

    def parse_locexpression(self, string, languages=None):
        '''Parse STRING as an expression, and include location records.'''
        return parse_expression(string, languages)

    def parse_expression(self, string, languages=None):
        '''Parse STRING as an expression.'''
        return delocust(parse_expression(string, languages))

    # XXX Unparse embedded languages?
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
            raise TypeError('Invalid expression: %s of type %s' %
                (repr(expression), type(expression)))

    def unparse_integer(self, integer):
        return str(integer)
    def unparse_string(self, string):
        return quote_string(string)
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
        'forget': [('directive_id', unparse_integer)],
        'labeled_forget': [('label', unparse_symbol)],
        'freeze': [('directive_id', unparse_integer)],
        'labeled_freeze': [('label', unparse_symbol)],
        'report': [('directive_id', unparse_integer)],
        'labeled_report': [('label', unparse_symbol)],
        'infer': [('expression', unparse_expression)],
        'clear': [],
        'list_directives': [],
        'get_directive': [('directive_id', unparse_integer)],
        'labeled_get_directive': [('label', unparse_symbol)],
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
                 'list_directives', 'get_directive', 'labeled_get_directive',
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
                chunks.append(self.unparse_expression_and_mark_up(instruction[key], expr_markers))
            else:
                chunks.append(unparser(self, instruction[key]))
        chunks.append(close_char)
        return ''.join(chunks)

    # XXX ???
    def parse_number(self, string):
        '''Parse STRING as an integer or real number.'''
        return float(string) if '.' in string else int(string)

    # XXX ???
    def split_program(self, string, languages=None):
        '''Split STRING into a sequence of instructions.

        Return a two-element list containing
        [0] a list of substrings, one for each instruction; and
        [1] a list of [start, end] positions of each instruction in STRING.
        '''
        ls = parse_instructions(string, languages)
        locs = [l['loc'] for l in ls]
        # XXX + 1?
        strings = [string[loc[0] : loc[1] + 1] for loc in locs]
        # XXX Sort??
        sortlocs = [list(sorted(loc)) for loc in locs]
        # XXX List???
        return [strings, sortlocs]

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
