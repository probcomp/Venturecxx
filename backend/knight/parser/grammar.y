/*
 * Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
 *
 * This file is part of Venture.
 *
 * Venture is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * Venture is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Venture.  If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * Metaprob grammar
 *
 * Terminal conventions:
 * - T_ means a punctuation token.
 * - K_ means a keyword, which might be used as a name if unambiguous.
 * - L_ means a lexeme, which has useful associated text, e.g. an integer.
 *
 * Exceptions:
 * - T_TRUE and T_FALSE because there's no context in which it is
 *   sensible to use them as a name -- anywhere you could refer to a
 *   name, `true' or `false' would mean the boolean.
 */

metaprob(top)		::= statements(ss).

statements(one)		::= statement(s).
statements(many)	::= statements(ss) T_SEMI(semi) statement(s).

statement(assign)	::= L_NAME(n) T_EQDEF(eq) expression(e).
statement(letvalues)	::= K_LET(l) T_LROUND(po) paramlist(names) T_RROUND(pc)
				T_EQDEF(eq) expression(e).
statement(none)		::= expression(e).

expression(top)		::= arrow(e).

arrow(one)		::= L_NAME(param) T_RARR(op) expression(body).
arrow(tuple)		::= T_LROUND(po) arraybody(params) T_RROUND(pc)
				T_RARR(op) expression(body).
arrow(none)		::= boolean_or(e).

boolean_or(or)		::= boolean_or(l) K_OR|T_OR(op) boolean_and(r).
boolean_or(none)	::= boolean_and(e).

boolean_and(and)	::= boolean_and(l) K_AND|T_AND(op) equality(r).
boolean_and(none)	::= equality(e).

equality(eq)		::= equality(l) K_EQ|T_EQ(op) comparison(r).
equality(neq)		::= equality(l) K_NEQ|T_NEQ(op) comparison(r).
equality(none)		::= comparison(e).

comparison(lt)		::= comparison(l) K_LT|T_LT(op) additive(r).
comparison(le)		::= comparison(l) K_LE|T_LE(op) additive(r).
comparison(ge)		::= comparison(l) K_GE|T_GE(op) additive(r).
comparison(gt)		::= comparison(l) K_GT|T_GT(op) additive(r).
comparison(none)	::= additive(e).

additive(add)		::= additive(l) K_ADD|T_ADD(op) multiplicative(r).
additive(sub)		::= additive(l) K_SUB|T_SUB(op) multiplicative(r).
additive(none)		::= multiplicative(e).

multiplicative(mul)	::= multiplicative(l) K_MUL|T_MUL(op) unary(r).
multiplicative(div)	::= multiplicative(l) K_DIV|T_DIV(op) unary(r).
multiplicative(none)	::= unary(e).

unary(pos)		::= T_ADD(op) unary(e).
unary(neg)		::= T_SUB(op) unary(e).
unary(none)		::= exponential(e).

exponential(pow)	::= applicative(l) K_POW|T_POW(op) exponential(r).
exponential(none)	::= applicative(e).

applicative(app)	::= applicative(fn) T_LROUND(o) arglist(args)
				T_RROUND(c).
applicative(lookup)	::= applicative(a) T_LSQUARE(o) expression(index)
				T_RSQUARE(c).
applicative(none)	::= primary(e).

arglist(none)		::= .
arglist(some)		::= args(args).
args(one)		::= tagged(arg).
args(many)		::= args(args) T_COMMA tagged(arg).

tagged(none)		::= expression(e).
tagged(kw)		::= L_NAME(name) T_COLON(colon) expression(e).

primary(paren)		::= T_LROUND(o) arraybody(es) T_RROUND(c).
primary(brace)		::= T_LCURLY(o) statements(ss) T_RCURLY(c).
primary(if)		::= K_IF(k) T_LROUND(po) expression(p) T_RROUND(pc)
				T_LCURLY(co) statements(c) T_RCURLY(cc)
				K_ELSE(ke)
				T_LCURLY(ao) statements(a) T_RCURLY(ac).
primary(qquote)		::= T_LOXFORD(o) statements(b) T_ROXFORD(c).
primary(unquote)	::= T_LDOLLAR(op) primary(e).
primary(array)		::= T_LSQUARE(o) arraybody(a) T_RSQUARE(c).
primary(literal)	::= literal(l).
primary(symbol)		::= L_NAME(s).
primary(qsymbol)        ::= T_QUOTE(o) L_NAME(s) T_QUOTE(c).

paramlist(none)		::= .
paramlist(some)		::= params(params).
params(one)		::= L_NAME(param).
params(many)		::= params(params) T_COMMA(c) L_NAME(param).

arraybody(none)		::= .
arraybody(some)		::= arrayelts(es).
arraybody(somecomma)	::= arrayelts(es) T_COMMA(c).
arrayelts(one)		::= expression(e).
arrayelts(many)		::= arrayelts(es) T_COMMA(c) expression(e).

literal(true)		::= T_TRUE(t).
literal(false)		::= T_FALSE(f).
literal(integer)	::= L_INTEGER(v).
literal(real)		::= L_REAL(v).
literal(string)		::= L_STRING(v).
literal(json)		::= L_TAG(t) json(v) T_GT(c).
literal(json_error)	::= L_TAG(t) error T_GT(c).

json(string)		::= L_STRING(v).
json(integer)		::= L_INTEGER(v).
json(real)		::= REAL(v).
json(list)		::= json_list(l).
json(dict)		::= json_dict(d).

json_list(empty)	::= T_LSQUARE T_RSQUARE.
json_list(nonempty)	::= T_LSQUARE json_list_terms(ts) T_RSQUARE.
json_list(error1)	::= T_LSQUARE json_list_terms(ts) error T_RSQUARE.
json_list(error)	::= T_LSQUARE error T_RSQUARE.
json_list_terms(one)	::= json(t).
json_list_terms(many)	::= json_list_terms(ts) T_COMMA json(t).
json_list_terms(error)	::= error T_COMMA json(t).

json_dict(empty)	::= T_LCURLY T_RCURLY.
json_dict(nonempty)	::= T_LCURLY json_dict_entries(es) T_RCURLY.
json_dict(error)	::= T_LCURLY json_dict_entries(es) error T_RCURLY.
json_dict_entries(one)	::= json_dict_entry(e).
json_dict_entries(many)	::= json_dict_entries(es) T_COMMA json_dict_entry(e).
json_dict_entries(error)::= error T_COMMA json_dict_entry(e).
json_dict_entry(e)	::= T_STRING(key) T_COLON json(value).
json_dict_entry(error)	::= error T_COLON json(value).

/*
 * Allow all keywords to be treated as names where unambiguous.
 *
 * grep -o -E 'K_[A-Z0-9_]+' < grammar.y | sort -u | awk '{ print "\t" $0 }'
 */
%fallback L_NAME
	K_ADD
	K_AND
	K_DIV
	K_ELSE
	K_EQ
	K_GE
	K_GT
	K_IF
	K_LE
	K_LET
	K_LT
	K_MUL
	K_NEQ
	K_OR
	K_POW
	K_SUB
	.
