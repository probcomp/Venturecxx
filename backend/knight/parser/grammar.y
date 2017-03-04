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

metaprob(top)		::= statements(ss) T_SEMI.

statements(one)		::= statement(s).
statements(many)	::= statements(ss) T_SEMI statement(s).

statement(assign)	::= L_NAME(n) T_EQDEF expression(e).
statement(letvalues)	::= T_LROUND arraybody(pattern) T_RROUND
				T_EQDEF expression(e).
statement(tr_assign)	::= boolean_or(l) T_COLON T_EQDEF expression(r).
statement(none)		::= expression(e).

expression(top)		::= arrow(e).

arrow(tuple)		::= T_LROUND arraybody(params) T_RROUND
				T_RARR expression(body).
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

exponential(pow)	::= accessing(l) K_POW|T_POW(op) exponential(r).
exponential(none)	::= accessing(e).

accessing(one)		::= T_AT applicative(e).
accessing(none)		::= applicative(e).

applicative(app)	::= applicative(fn) T_LROUND arglist(args) T_RROUND.
applicative(lookup)	::= applicative(a) T_LSQUARE arraybody(index)
				T_RSQUARE.
applicative(none)	::= primary(e).

arglist(none)		::= .
arglist(some)		::= args(args).
args(one)		::= tagged(arg).
args(many)		::= args(args) T_COMMA tagged(arg).

tagged(none)		::= expression(e).
tagged(kw)		::= L_NAME(name) T_COLON expression(e).

primary(paren)		::= T_LROUND arraybody(items) T_RROUND.
primary(brace)		::= T_LCURLY statements(ss) T_RCURLY.
primary(if)		::= K_IF T_LROUND expression(p) T_RROUND
				T_LCURLY statements(c) T_RCURLY
				K_ELSE
				T_LCURLY statements(a) T_RCURLY.
primary(qquote)		::= T_LOXFORD(o) statements(b) T_ROXFORD(c).
primary(array)		::= T_LSQUARE arraybody(a) T_RSQUARE.
primary(qsymbol)        ::= T_QUOTE L_NAME(s) T_QUOTE.
primary(none)		::= trace(e).

trace(one)		::= T_LTRACE expression(e) T_RCURLY.
trace(filled)		::= T_LTRACE expression(e) T_COMMA entrylist(es) T_RCURLY.
trace(unfilled)		::= T_LTRACE entrylist(es) T_RCURLY.
trace(none)		::= name(e).

entrylist(none)		::= .
entrylist(some)		::= entries(es).
entries(one)		::= name(n) T_EQDEF expression(e).
entries(many)		::= entries(es) T_COMMA name(n) T_EQDEF expression(e).

name(unquote)		::= T_LDOLLAR(op) primary(e).
name(symbol)		::= L_NAME(s).
name(literal)		::= literal(l).

literal(true)		::= T_TRUE.
literal(false)		::= T_FALSE.
literal(integer)	::= L_INTEGER(v).
literal(real)		::= L_REAL(v).
literal(string)		::= L_STRING(v).

arraybody(none)		::= .
arraybody(some)		::= arrayelts(es).
arraybody(somecomma)	::= arrayelts(es) T_COMMA.
arrayelts(one)		::= expression(e).
arrayelts(splice)	::= T_MUL expression(e).
arrayelts(many)		::= arrayelts(es) T_COMMA expression(e).
arrayelts(many_splice)	::= arrayelts(es) T_COMMA T_MUL expression(e).

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
	K_LT
	K_MUL
	K_NEQ
	K_OR
	K_POW
	K_SUB
	.
