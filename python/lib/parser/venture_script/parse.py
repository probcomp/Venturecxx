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

import numbers
import StringIO
import json

from venture.exception import VentureException
import venture.lite.value as vv
import venture.value.dicts as val

from venture.parser import ast
from venture.parser.venture_script import grammar
from venture.parser.venture_script import scan

def locquoted(located_quoter, located_value, f):
    (vstart, vend) = located_value.loc
    (start, _end) = located_quoter.loc
    assert start < vstart
    return ast.Located([start, vend], f(located_value))

def delocust(l):
    "Recursively remove location tags."
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

def adjlocust(l, o):
    "Recursively shift location tags by the given offset."
    start, end = l.loc
    v = l.value
    if isinstance(v, list) or isinstance(v, tuple):
        v = [adjlocust(u, o) for u in v]
    return ast.Located([start + o, end + o], v)

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
    def syntax_error(self, (number, located)):
        # XXX Should not raise here -- should accumulate errors and
        # report them all at the end.
        #
        # XXX Should adapt lemonade to support passing a message, and
        # make the generated parser say which tokens (and, ideally,
        # nonterminals) it was expecting instead.
        text = located.value
        (start, end) = located.loc
        raise VentureException('text_parse',
            ('Syntax error at %s (token %d)' % (repr(text), number)),
            text_index=[start, end])

    # Venture start symbol: store result in self.answer, return none.
    def p_venture_top(self, insts):
        for i in insts:
            assert ast.isloc(i)
        self.answer = insts

    # instructions: Return list of located instructions.
    def p_instructions_none(self):
        return []
    def p_instructions_some(self, insts, inst):
        if inst is not None:
            assert ast.isloc(inst)
            insts.append(inst)
        return insts

    # instruction_opt: Return located instruction or None.
    def p_instruction_opt_none(self):
        return None
    def p_instruction_opt_some(self, inst):
        assert ast.isloc(inst)
        return inst

    # instruction: Return located {'instruction': 'foo', ...}.
    def p_instruction_command(self, c):
        assert ast.isloc(c)
        return c
    def p_instruction_statement(self, e):
        i = ast.update_value(e, 'evaluate')
        return ast.update_value(e, {'instruction': i, 'expression': e})

    # labelled: Return located expression.
    def p_labelled_directive(self, l, d):
        label = ast.map_value(val.symbol, l)
        exp = d.value
        new_exp = exp + [label]
        new_d = ast.locmerge(label, d, new_exp)
        return new_d
    def p_labelled_directive_prog(self, dol, lab_exp, d):
        label = ast.locmerge(dol, lab_exp, val.unquote(lab_exp))
        exp = d.value
        new_exp = exp + [label]
        new_d = ast.locmerge(label, d, new_exp)
        return new_d

    # directive: Return located expression.
    def p_directive_assume(self, k, n, eq, e):
        assert ast.isloc(e)
        i = ast.update_value(k, val.symbol('assume'))
        s = ast.map_value(val.symbol, n)
        app = [i, s, e]
        return ast.locmerge(i, e, app)
    def p_directive_assume_prog(self, k, dol, sym_exp, eq, e):
        assert ast.isloc(e)
        assert ast.isloc(sym_exp)
        i = ast.update_value(k, val.symbol('assume'))
        app = [i, ast.locmerge(dol, sym_exp, val.unquote(sym_exp)), e]
        return ast.locmerge(i, e, app)
    def p_directive_observe(self, k, e, eq, e1):
        assert ast.isloc(e)
        assert ast.isloc(e1)
        i = ast.update_value(k, val.symbol('observe'))
        app = [i, e, e1]
        return ast.locmerge(i, e1, app)
    def p_directive_predict(self, k, e):
        assert ast.isloc(e)
        i = ast.update_value(k, val.symbol('predict'))
        app = [i, e]
        return ast.locmerge(i, e, app)

    # command: Return located { 'instruction': located(..., 'foo'), ... }.
    def p_command_define(self, k, n, eq, e):
        assert ast.isloc(e)
        i = ast.update_value(k, 'define')
        s = ast.map_value(val.symbol, n)
        return ast.locmerge(i, e, {'instruction': i, 'symbol': s, 'expression': e})
    def p_command_infer(self, k, e):
        assert ast.isloc(e)
        i = ast.update_value(k, 'infer')
        return ast.locmerge(i, e, {'instruction': i, 'expression': e})
    def p_command_load(self, k, pathname):
        i = ast.update_value(k, 'load')
        return ast.locmerge(i, pathname, {'instruction': i, 'file': pathname})

    # body: Return located expression.
    def p_body_do(self, ss, semi, e):
        assert ast.isloc(ss)
        if e is None:
            e = ast.update_value(semi, val.symbol('pass'))
        assert ast.isloc(e)
        do = ast.locmerge(ss, e, val.symbol('do'))
        return ast.locmerge(ss, e, [do] + ss.value + [e])
    def p_body_exp(self, e):
        assert ast.isloc(e)
        return e

    # statements: Return located list of located bindings.
    def p_statements_one(self, s):
        assert ast.isloc(s)
        return ast.update_value(s, [s])
    def p_statements_many(self, ss, semi, s):
        assert ast.isloc(s)
        assert ast.isloc(s)
        ss.value.append(s)
        return ast.locmerge(ss, s, ss.value)

    # statement: Return located statement
    def p_statement_let(self, l, n, eq, e):
        assert ast.isloc(e)
        let = ast.update_value(l, val.symbol('let'))
        n = ast.map_value(val.symbol, n)
        return ast.locmerge(let, e, [let, n, e])
    def p_statement_assign(self, n, eq, e):
        assert ast.isloc(e)
        let = ast.update_value(eq, val.symbol('let'))
        n = ast.map_value(val.symbol, n)
        return ast.locmerge(n, e, [let, n, e])
    def p_statement_letrec(self, l, n, eq, e):
        assert ast.isloc(e)
        let = ast.update_value(l, val.symbol('letrec'))
        n = ast.map_value(val.symbol, n)
        return ast.locmerge(let, e, [let, n, e])
    def p_statement_mutrec(self, l, n, eq, e):
        assert ast.isloc(e)
        let = ast.update_value(l, val.symbol('mutrec'))
        n = ast.map_value(val.symbol, n)
        return ast.locmerge(let, e, [let, n, e])
    def p_statement_letvalues(self, l, po, names, pc, eq, e):
        assert ast.isloc(e)
        assert all(map(ast.isloc, names))
        let = ast.update_value(l, val.symbol('let_values'))
        names = ast.locmerge(po, pc, names)
        return ast.locmerge(let, e, [let, names, e])
    def p_statement_labelled(self, d):
        assert ast.isloc(d)
        return d
    def p_statement_none(self, e):
        assert ast.isloc(e)
        return e

    # expression_opt: Return located expression or None.
    def p_expression_opt_none(self):
        return None
    def p_expression_opt_some(self, e):
        assert ast.isloc(e)
        return e

    def _p_binop(self, l, op, r):
        assert ast.isloc(l)
        assert ast.isloc(r)
        assert op.value in operators
        app = [ast.map_value(val.symbol, ast.update_value(op, operators[op.value])), l, r]
        return ast.locmerge(l, r, app)
    def _p_exp(self, e):
        assert ast.isloc(e)
        return e

    # expression: Return located expression.
    p_expression_top = _p_exp
    def p_do_bind_bind(self, n, op, e):
        assert ast.isloc(e)
        # XXX Yes, this remains infix, for the macro expander to handle...
        # XXX Convert <~ to <- for the macro expander's sake
        return ast.locmerge(n, e, [n, ast.update_value(op, val.symbol("<-")), e])
    def p_do_bind_labelled(self, n, op, l):
        assert ast.isloc(l)
        # XXX Yes, this remains infix, for the macro expander to handle...
        # XXX Convert <~ to <- for the macro expander's sake
        return ast.locmerge(n, l, [n, ast.update_value(op, val.symbol("<-")), l])
    def p_action_directive(self, d):
        assert ast.isloc(d)
        return d
    def p_action_force(self, k, e1, eq, e2):
        assert ast.isloc(e1)
        assert ast.isloc(e2)
        i = ast.update_value(k, val.symbol('force'))
        app = [i, e1, e2]
        return ast.locmerge(i, e2, app)
    def p_action_sample(self, k, e):
        assert ast.isloc(e)
        i = ast.update_value(k, val.symbol('sample'))
        app = [i, e]
        return ast.locmerge(i, e, app)
    def p_arrow_one(self, param, op, body):
        assert ast.isloc(body)
        param = ast.map_value(val.symbol, param)
        return ast.locmerge(param, body, [
            ast.map_value(val.symbol, ast.update_value(op, 'lambda')),
            ast.update_value(param, [param]),
            body,
        ])
    def p_arrow_tuple(self, po, params, pc, op, body):
        assert ast.isloc(body)
        return ast.locmerge(po, body, [
            ast.map_value(val.symbol, ast.update_value(op, 'lambda')),
            ast.locmerge(po, pc, params),
            body,
        ])

    def p_path_expression_one(self, slash, s):
        assert ast.isloc(s)
        top = ast.update_value(slash, val.symbol('by_top'))
        intersect = ast.update_value(slash, val.symbol('by_walk'))
        app = [intersect, ast.loclist([top]), s]
        return ast.locmerge(top, s, app)

    def p_path_expression_some(self, more, slash, s):
        # XXX Is this just _p_binop with the "slash" operator?
        assert ast.isloc(s)
        intersect = ast.update_value(slash, val.symbol('by_walk'))
        app = [intersect, more, s]
        return ast.locmerge(more, s, app)

    def p_path_step_tag(self, q, tag):
        by_tag = ast.update_value(q, val.symbol('by_tag'))
        name = locquoted(q, tag, val.quasiquote)
        app = [by_tag, name]
        return ast.locmerge(by_tag, name, app)

    def p_path_step_tag_val(self, q, tag, eq, value):
        by_tag_value = ast.update_value(q, val.symbol('by_tag_value'))
        name = locquoted(q, tag, val.quasiquote)
        app = [by_tag_value, name, value]
        return ast.locmerge(by_tag_value, value, app)

    def p_path_step_star(self, star):
        return ast.update_value(star, [val.symbol('by_star')])

    def p_hash_tag_tag(self, e, h, tag):
        tag_proc = ast.update_value(h, val.symbol('tag'))
        name = locquoted(h, tag, val.quasiquote)
        value = ast.update_value(h, val.string("default"))
        app = [tag_proc, name, value, e]
        return ast.locmerge(e, tag_proc, app)

    def p_hash_tag_tag_val(self, e, h, tag, colon, value):
        tag_proc = ast.update_value(h, val.symbol('tag'))
        name = locquoted(h, tag, val.quasiquote)
        app = [tag_proc, name, value, e]
        return ast.locmerge(e, value, app)

    p_do_bind_none = _p_exp
    p_action_none = _p_exp
    p_arrow_pathexp = _p_exp
    p_arrow_none = _p_exp
    p_path_step_edge = _p_exp
    p_hash_tag_none = _p_exp
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
    p_unary_none = _p_exp
    p_exponential_pow = _p_binop
    p_exponential_none = _p_exp

    def p_unary_pos(self, op, e):
        return self._p_binop(ast.update_value(op, val.number(0)), op, e)
    def p_unary_neg(self, op, e):
        return self._p_binop(ast.update_value(op, val.number(0)), op, e)

    def p_applicative_app(self, fn, o, args, c):
        assert ast.isloc(fn)
        for arg in args:
            assert ast.isloc(arg)
        return ast.locmerge(fn, c, [fn] + args)
    def p_applicative_lookup(self, a, o, index, c):
        assert ast.isloc(a)
        assert ast.isloc(index)
        lookup = ast.update_value(o, val.sym('lookup'))
        return ast.locmerge(a, c, [lookup, a, index])
    def p_applicative_none(self, e):
        assert ast.isloc(e)
        return e

    # arglist, args: Return list of located expressions.
    def p_arglist_none(self):           return []
    def p_arglist_some(self, args):     return args
    def p_args_one(self, arg):          return [arg]
    def p_args_many(self, args, arg):   args.append(arg); return args
    def p_tagged_none(self, e):         return e
    def p_tagged_kw(self, name, colon, e): return e

    def p_primary_paren(self, o, es, c):
        assert isinstance(es, list) and all(map(ast.isloc, es))
        if len(es) == 1:
            [e] = es
            return ast.locmerge(o, c, e.value)
        else:
            construction = [ast.map_value(val.symbol, ast.update_value(o, 'values_list'))] + es
            return ast.locmerge(o, c, construction)
    def p_primary_brace(self, o, e, c):
        assert ast.isloc(e)
        return ast.locmerge(o, c, e.value)
    def p_primary_proc(self, k, po, params, pc, bo, body, bc):
        assert ast.isloc(body)
        return ast.locmerge(k, bc, [
            ast.map_value(val.symbol, ast.update_value(k, 'proc')),
            ast.locmerge(po, pc, params),
            body,
        ])
    def p_primary_if(self, k, po, p, pc, co, c, cc, ke, ao, a, ac):
        assert ast.isloc(p)
        assert ast.isloc(c)
        assert ast.isloc(a)
        return ast.locmerge(k, ac,
            [ast.map_value(val.symbol, ast.update_value(k, 'if')), p, c, a])
    def p_primary_qquote(self, o, b, c):
        return ast.locmerge(o, c, val.quasiquote(b))
    def p_primary_unquote(self, op, e):
        return ast.locmerge(op, e,
            val.quote(ast.locmerge(op, e, val.unquote(e))))
    def p_primary_array(self, o, a, c):
        assert isinstance(a, list)
        construction = [ast.map_value(val.symbol, ast.update_value(o, 'array'))] + a
        return ast.locmerge(o, c, construction)
    def p_primary_literal(self, l):
        assert ast.isloc(l)
        return l
    def p_primary_symbol(self, s):
        return ast.map_value(val.symbol, s)
    def p_primary_qsymbol(self, o, s, c):
        return ast.locmerge(o, c, val.quote(val.symbol(s.value)))
    def p_primary_language(self, ll):
        assert ast.isloc(ll), '%r' % (ll,)
        l = ll.value
        (start, _end) = ll.loc
        assert ast.isloc(l), '%r' % (l,)
        l_ = adjlocust(l, start)
        return l_

    # paramlist, params: Return list of located symbols.
    def p_paramlist_none(self):                 return []
    def p_paramlist_some(self, params):         return params
    def p_params_one(self, param):
        return [ast.map_value(val.symbol, param)]
    def p_params_many(self, params, c, param):
        params.append(ast.map_value(val.symbol, param))
        return params

    # arraybody, arrayelts: Return list of located expressions.
    def p_arraybody_none(self):                 return []
    def p_arraybody_some(self, es):             return es
    def p_arrayelts_one(self, e):               return [e]
    def p_arrayelts_many(self, es, c, e):       es.append(e); return es

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
    def p_literal_json(self, t, v, c):
        t0 = t.value
        start, end = t.loc
        assert t0[-1] == '<'
        t0 = t0[:-1]
        if t0 == 'boolean':
            # XXX Accumulate parse error.
            raise VentureException('text_parse',
                ('JSON not allowed for %s' % (t0,)),
                text_index=[start, end])
        return ast.locmerge(t, c, {'type': t0, 'value': v})

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
                loc = (scanner.cur_pos, scanner.cur_pos)
                parser.feed((grammar.T_SEMI, ast.Located(loc, ';')))
            parser.feed(token)
        if token[0] == 0:       # EOF
            break
    assert isinstance(semantics.answer, list)
    for i in semantics.answer:
        assert ast.isloc(i)
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
                semi = ast.Located([scanner.cur_pos, scanner.cur_pos], ';')
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
    return map(ast.as_legacy_dict, parse_string(string, languages))

def parse_instruction(string, languages=None):
    ls = parse_instructions(string, languages)
    if len(ls) != 1:
        raise VentureException('text_parse', "Expected a single instruction.  String:\n'%s'\nParse:\n%s" % (string, ls))
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
        elif isinstance(expression, vv.VentureValue):
            return value_to_string(expression.asStackDict(None))
        elif isinstance(expression, numbers.Number):
            return str(expression)
        elif isinstance(expression, basestring):
            # XXX This is due to &@!#^&$@!^$&@#!^%&*.
            return expression
        elif isinstance(expression, list):
            terms = (self.unparse_expression(e) for e in expression)
            proc = terms.next()
            return proc + '(' + ', '.join(terms) + ')'
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
        chunks = []
        if 'label' in instruction and 'label' not in (k for k,_u in unparsers):
            chunks.append(instruction['label']['value'])
            chunks.append(': ')
        if i[0 : len('labeled_')] == 'labeled_':
            chunks.append(i[len('labeled_'):])
        else:
            chunks.append(i)
        def append_unparsed(key, unparser):
            chunks.append(' ')
            if key == 'expression': # Urk
                chunks.append(self.unparse_expression_and_mark_up(instruction[key], expr_markers))
            else:
                chunks.append(unparser(self, instruction[key]))
        if len(unparsers) >= 1:
            append_unparsed(*unparsers[0])
        if len(unparsers) >= 2:
            chunks.append(' =')
            append_unparsed(*unparsers[1])
        for key, unparser in unparsers[2:]:
            append_unparsed(key, unparser)
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
