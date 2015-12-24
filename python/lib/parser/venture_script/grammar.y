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
 * Venture grammar (`VentureScript', JavaScript-style notation).
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

venture(top)		::= instructions(insts).

instructions(none)	::= .
instructions(some)	::= instructions(insts) instruction_opt(inst) T_SEMI.
instruction_opt(none)	::= .
instruction_opt(some)	::= instruction(inst).

instruction(labelled)	::= L_NAME(l) T_COLON directive(d).
instruction(unlabelled)	::= directive(d).
instruction(command)	::= command(c).
instruction(expression)	::= expression(e).

directive(define)	::= K_DEFINE(k) L_NAME(n) T_EQDEF(eq) expression(e).
directive(assume)	::= K_ASSUME(k) L_NAME(n) T_EQDEF(eq) expression(e).
directive(observe)	::= K_OBSERVE(k) expression(e) T_EQDEF(eq) literal(v).
directive(predict)	::= K_PREDICT(k) expression(e).

command(infer)		::= K_INFER(k) expression(e).
command(get_directive)	::= K_GET(k0) K_DIRECTIVE(k1) directive_ref(dr).
command(force)		::= K_FORCE(k) expression(e) T_EQDEF(eq) literal(v).
command(sample)		::= K_SAMPLE(k) expression(e).
/* XXX are these commands supposed to be one keyword or three? */
command(continuous_inference_status)	::= K_CONTINUOUS_INFERENCE_STATUS(k).
command(start_continuous_inference)	::= K_START(k0) K_CONTINUOUS(k1)
						K_INFERENCE(k2).
command(stop_continuous_inference)	::= K_STOP_CONTINUOUS_INFERENCE(k).
command(get_current_exception)		::= K_GET(k0) K_CURRENT(k1)
						K_EXCEPTION(k2).
command(get_state)		::= K_GET(k0) K_STATE(k1).
command(get_global_logscore)	::= K_GET(k0) K_GLOBAL(k1) K_LOGSCORE(k2).
command(load)		::= K_LOAD(k) L_STRING(pathname).

directive_ref(numbered)	::= L_INTEGER(number).
directive_ref(labelled)	::= L_NAME(label).

body(let)		::= let(l) T_SEMI(semi) expression(e).
body(exp)		::= expression(e).
let(one)		::= let1(l).
let(many)		::= let(ls) T_SEMI(semi) let1(l).
let1(l)			::= L_NAME(n) T_EQDEF(eq) expression(e).

expression(top)		::= do_bind(e).

do_bind(bind)		::= L_NAME(n) T_LARR(op) expression(e).
do_bind(none)		::= boolean_and(e).

/* XXX This AND/OR precedence is backwards from everyone else!  */
boolean_and(and)	::= boolean_and(l) K_AND|T_AND(op) boolean_or(r).
boolean_and(none)	::= boolean_or(e).

boolean_or(or)		::= boolean_or(l) K_OR|T_OR(op) equality(r).
boolean_or(none)	::= equality(e).

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

multiplicative(mul)	::= multiplicative(l) K_MUL|T_MUL(op) exponential(r).
multiplicative(div)	::= multiplicative(l) K_DIV|T_DIV(op) exponential(r).
multiplicative(none)	::= exponential(e).

exponential(pow)	::= applicative(l) K_POW|T_POW(op) exponential(r).
exponential(none)	::= applicative(e).

applicative(app)	::= applicative(fn) T_LROUND(o) arglist(args)
				T_RROUND(c).
applicative(none)	::= primary(e).

arglist(none)		::= .
arglist(some)		::= args(args).
args(one)		::= expression(arg).
args(many)		::= args(args) T_COMMA expression(arg).

primary(paren)		::= T_LROUND(o) body(e) T_RROUND(c).
primary(brace)		::= T_LCURLY(o) let(l) T_SEMI(semi) expression(e)
				T_RCURLY(c).
primary(proc)		::= K_PROC(k)
				T_LROUND(po) paramlist(params) T_RROUND(pc)
				T_LCURLY(bo) body(body) T_RCURLY(bc).
primary(if)		::= K_IF(k) T_LROUND(po) body(p) T_RROUND(pc)
				T_LCURLY(co) body(c) T_RCURLY(cc)
				K_ELSE(ke)
				T_LCURLY(ao) body(a) T_RCURLY(ac).
primary(literal)	::= literal(l).
primary(symbol)		::= L_NAME(s).

paramlist(none)		::= .
paramlist(some)		::= params(params).
params(one)		::= L_NAME(param).
params(many)		::= params(params) T_COMMA(c) L_NAME(param).

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
	K_ASSUME
	K_CONTINUOUS
	K_CURRENT
	K_DEFINE
	K_DIRECTIVE
	K_DIV
	K_ELSE
	K_EQ
	K_EXCEPTION
	K_FORCE
	K_GE
	K_GET
	K_GLOBAL
	K_GT
	K_IF
	K_INFER
	K_INFERENCE
	K_LE
	K_LOAD
	K_LOGSCORE
	K_LT
	K_MUL
	K_NEQ
	K_OBSERVE
	K_OR
	K_POW
	K_PREDICT
	K_PROC
	K_SAMPLE
	K_START
	K_STATE
	K_STATUS
	K_STOP
	K_SUB
	.

/* Reserved.  */
%nonassoc	K_LAMBDA.
