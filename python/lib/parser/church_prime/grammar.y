/*
 * Copyright (c) 2014, MIT Probabilistic Computing Project.
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
 * Venture grammar (`Church prime', Lisp-style notation).
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

venture(empty)		::= .
venture(i)		::= instructions(insts).
venture(e)		::= expression(exp).

instructions(one)	::= instruction(inst).
instructions(many)	::= instructions(insts) instruction(inst).

instruction(labelled)	::= L_NAME(l) T_COLON
				T_LSQUARE(open) directive(d) T_RSQUARE(close).
instruction(unlabelled)	::= T_LSQUARE(open) directive(d) T_RSQUARE(close).
instruction(command)	::= T_LSQUARE(open) command(c) T_RSQUARE(close).
instruction(laberror)	::= error T_COLON(colon)
				T_LSQUARE(open) directive(d) T_RSQUARE(close).
instruction(direrror)	::= L_NAME(l) T_COLON(colon)
				T_LSQUARE(open) error T_RSQUARE(close).
instruction(labdirerror)::= error T_COLON(colon)
				T_LSQUARE(open) error T_RSQUARE(close).
instruction(error)	::= T_LSQUARE(open) error T_RSQUARE(close).

/*
 * The following directive and command production rules are
 * substantially more detailed than they need to be.
 *
 * This has the nice property they detect usage mistakes early on, in
 * the parser: e.g., you can't write a non-literal expression on the
 * right-hand side of OBSERVE.
 *
 * This has the not-so-nice property that the set of directives and
 * commands is not as easily as extensible as one might like.  But
 * that is not a regression from the previous Venture parser, so I
 * won't worry too much about it just yet.
 */

directive(define)	::= K_DEFINE(k) L_NAME(n) expression(e).
directive(assume)	::= K_ASSUME(k) L_NAME(n) expression(e).
directive(observe)	::= K_OBSERVE(k) expression(e) literal(v).
directive(predict)	::= K_PREDICT(k) expression(e).

command(configure)	::= K_CONFIGURE(k) json(options).
command(forget)		::= K_FORGET(k) directive_ref(dr).
command(report)		::= K_REPORT(k) directive_ref(dr).
command(infer)		::= K_INFER(k) expression(e).
command(clear)		::= K_CLEAR(k).
command(rollback)	::= K_ROLLBACK(k).
command(list_directives)::= K_LIST_DIRECTIVES(k).
command(get_directive)	::= K_GET_DIRECTIVE(k) directive_ref(dr).
command(force)		::= K_FORCE(k) expression(e) literal(v).
command(sample)		::= K_SAMPLE(k) expression(e).
command(continuous_inference_status)	::= K_CONTINUOUS_INFERENCE_STATUS(k).
command(start_continuous_inference)	::= K_START_CONTINUOUS_INFERENCE(k)
						expression(e).
command(stop_continuous_inference)	::= K_STOP_CONTINUOUS_INFERENCE(k).
command(get_current_exception)		::= K_GET_CURRENT_EXCEPTION(k).
command(get_state)		::= K_GET_STATE(k).
command(get_logscore)		::= K_GET_LOGSCORE(k) directive_ref(d).
command(get_global_logscore)	::= K_GET_GLOBAL_LOGSCORE(k).
command(profiler_configure)	::= K_PROFILER_CONFIGURE(k) json(options).
command(profiler_clear)		::= K_PROFILER_CLEAR(k).
command(profiler_list_random)	::= K_PROFILER_LIST_RANDOM(k) K_CHOICES.
command(load)			::= K_LOAD(k) json(pathname).

directive_ref(numbered)	::= L_INTEGER(number).
directive_ref(labelled)	::= L_NAME(label).

expression(symbol)	::= L_NAME(name).
expression(operator)	::= L_OPERATOR(op).
expression(literal)	::= literal(value).
expression(combination)	::= T_LROUND(open) expressions(es) T_RROUND(close).
expression(comb_error)	::= T_LROUND(open) expressions(es) error
				T_RROUND(close).

expressions(none)	::= .
expressions(some)	::= expressions(es) expression(e).

literal(true)		::= T_TRUE(t).
literal(false)		::= T_FALSE(f).
literal(integer)	::= L_INTEGER(v).
literal(real)		::= L_REAL(v).
literal(json)		::= L_NAME(type)
				T_LANGLE(open) json(value) T_RANGLE(close).
literal(json_error)	::= L_NAME(type) T_LANGLE(open) error T_RANGLE(close).

json(string)		::= L_STRING(v).
json(integer)		::= L_INTEGER(v).
json(real)		::= L_REAL(v).
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
json_dict_entry(e)	::= L_STRING(key) T_COLON json(value).
json_dict_entry(error)	::= error T_COLON json(value).

/*
 * Treat < and > as operators rather than angle-brackets where
 * unambiguous.
 */
%fallback L_OPERATOR
	T_LANGLE
	T_RANGLE
	.

/*
 * Allow all keywords to be treated as names where unambiguous.
 *
 * grep -o -E 'K_[A-Z0-9_]+' < grammar.y | sort -u | awk '{ print "\t" $0 }'
 */
%fallback L_NAME
	K_ASSUME
	K_CHOICES
	K_CLEAR
	K_CONFIGURE
	K_CONTINUOUS_INFERENCE_STATUS
	K_FORCE
	K_FORGET
	K_GET_CURRENT_EXCEPTION
	K_GET_DIRECTIVE
	K_GET_GLOBAL_LOGSCORE
	K_GET_LOGSCORE
	K_GET_STATE
	K_INFER
	K_LIST_DIRECTIVES
	K_LOAD
	K_OBSERVE
	K_PREDICT
	K_PROFILER_CLEAR
	K_PROFILER_CONFIGURE
	K_PROFILER_LIST_RANDOM
	K_REPORT
	K_ROLLBACK
	K_SAMPLE
	K_START_CONTINUOUS_INFERENCE
	K_STOP_CONTINUOUS_INFERENCE
	.
