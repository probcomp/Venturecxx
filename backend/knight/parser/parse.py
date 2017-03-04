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

import venture.lite.value as vv

from venture.knight.parser import grammar
from venture.knight.parser import scan
from venture.knight.types import App
from venture.knight.types import Def
from venture.knight.types import Lam
from venture.knight.types import Lit
from venture.knight.types import Seq
from venture.knight.types import Spl
from venture.knight.types import Tra
from venture.knight.types import Tup
from venture.knight.types import Var

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
        raise Exception('Syntax error!')
    def syntax_error(self, (number, item)):
        # XXX Should not raise here -- should accumulate errors and
        # report them all at the end.
        #
        # XXX Should adapt lemonade to support passing a message, and
        # make the generated parser say which tokens (and, ideally,
        # nonterminals) it was expecting instead.
        raise Exception('Syntax error at %s (token %d)' % (repr(item), number))

    # Metaprob start symbol: store result in self.answer, return none.
    def p_metaprob_top(self, ss):
        self.answer = ss

    # statements: Return a Seq expression
    def p_statements_one(self, s):
        return Seq([s])
    def p_statements_many(self, ss, s):
        assert isinstance(ss, Seq)
        ss.subs.append(s)
        return ss

    # statement: Return an expression
    def p_statement_assign(self, n, e):
        return Def(Var(n), e)
    def p_statement_letvalues(self, pattern, e):
        return Def(Seq(pattern), e)
    def p_statement_tr_assign(self, l, r):
        return App([Var('trace_set'), l, r])
    def p_statement_none(self, e):
        return e

    def _p_binop(self, l, op, r):
        if op in operators:
            # Perform operator substitution
            new_op = Var(operators[op])
        else:
            # Leave it
            new_op = Var(op)
        return App([new_op, l, r])
    def _p_exp(self, e):
        return e

    # expression: Return expression.
    p_expression_top = _p_exp
    def p_arrow_tuple(self, params, body):
        assert isinstance(params, list)
        for p in params:
            assert isinstance(p, Var)
        return Lam([p.name for p in params], body)

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
    p_unary_none = _p_exp
    p_exponential_pow = _p_binop
    p_exponential_none = _p_exp
    p_accessing_none = _p_exp

    def p_unary_pos(self, op, e):
        return self._p_binop(Lit(0), op, e)
    def p_unary_neg(self, op, e):
        return self._p_binop(Lit(0), op, e)

    def p_accessing_one(self, e):
        return App([Var('trace_get'), e])

    def p_applicative_app(self, fn, args):
        return App([fn] + args)
    def p_applicative_lookup(self, a, index):
        return App([Var('lookup_chain'), a, App([Var('list')] + index)])
    def p_applicative_none(self, e):
        return e

    # arglist, args: Return list of expressions.
    def p_arglist_none(self):           return []
    def p_arglist_some(self, args):     return args
    def p_args_one(self, arg):          return [arg]
    def p_args_many(self, args, arg):   args.append(arg); return args
    def p_tagged_none(self, e):         return e
    def p_tagged_kw(self, name, e):     return e

    def p_primary_paren(self, items):
        if len(items) == 1:
            return items[0]
        else:
            return Tup(items)
    def p_primary_brace(self, ss):
        assert isinstance(ss, Seq)
        return ss
    def p_primary_if(self, p, c, a):
        return App([App([Var('biplex'), p, Lam([], c), Lam([], a)])])
    def p_primary_qquote(self, o, b, c):
        # XXX Options:
        # - Make a Quasi syntax and interpret it somewhere
        # - Make it App([Var("quasiquote"), ...]) and interpret that somewhere
        raise Exception("quasiquotation is not supported yet")
    def p_primary_array(self, a):
        assert isinstance(a, list)
        return App([Var("array")] + a)
    def p_primary_qsymbol(self, s):
        return Lit(vv.VentureSymbol(s))
    p_primary_none = _p_exp

    def p_trace_one(self, e):
        return Tra(e, [])
    def p_trace_filled(self, e, es):
        return Tra(e, es)
    def p_trace_unfilled(self, es):
        return Tra(None, es)
    p_trace_none = _p_exp

    def p_entrylist_none(self):         return []
    def p_entrylist_some(self, es):     return es
    def p_entries_one(self, n, e):      return [(n, e)]
    def p_entries_many(self, es, n, e): es.append((n, e)); return es

    def p_name_unquote(self, op, e):
        raise Exception("quasiquotation is not supported yet")
    def p_name_symbol(self, s):
        return Var(s)
    def p_name_literal(self, l):
        return l

    # literal: Return `Lit'.
    def p_literal_true(self):
        return Lit(vv.VentureBool(True))
    def p_literal_false(self):
        return Lit(vv.VentureBool(False))
    def p_literal_integer(self, v):
        return Lit(vv.VentureInteger(v))
    def p_literal_real(self, v):
        return Lit(vv.VentureNumber(v))
    def p_literal_string(self, v):
        return Lit(vv.VentureString(v))

    # arraybody, arrayelts: Return list of expressions.
    def p_arraybody_none(self):                 return []
    def p_arraybody_some(self, es):             return es
    def p_arraybody_somecomma(self, es):        return es
    def p_arrayelts_one(self, e):               return [e]
    def p_arrayelts_splice(self, e):            return [Spl(e)]
    def p_arrayelts_many(self, es, e):          es.append(e); return es
    def p_arrayelts_many_splice(self, es, e):   es.append(Spl(e)); return es

def parse(f, context):
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
    assert isinstance(semantics.answer, Seq)
    return semantics.answer

def parse_string(string):
    return parse(StringIO.StringIO(string), '(string)')
