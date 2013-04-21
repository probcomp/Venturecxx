#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re


def _collapse_identity(toks, operators):
    """
    Removes one layer of nested identity functions if the
    inner expression is a function application contained
    in the list of operators. For example:

    _collapse_identity(
        ['identity',
            ['identity',
                ['+', a, b]]],
        ('+'))

    returns: ['identity',
                ['+',a, b]]
    """
    if not isinstance(toks, (list, tuple)):
        return toks
    if not toks[0] == 'identity':
        return toks
    if not isinstance(toks[1], (list, tuple)):
        return toks
    if toks[1][0] == 'identity':
        return ['identity', _collapse_identity(toks[1], operators)]
    if toks[1][0] in operators:
        return toks[1]
    return toks

def _make_infix_token(previous_token, operator_map, lower_precedence, left_to_right = True, swap_order = False):
    """
    generate a token that matches an infix expression and parses it accordingly
    """
    operator_dict = dict(operator_map)
    operator_key_list = list(x[0] for x in operator_map)
    operator_value_list = list(x[1] for x in operator_map)
    def f(s, loc, toks):
        """
        generates a function that processes a list of infix tokens into
        the proper binary tree based on certain operator precedence rules
        """
        if len(toks) == 1:
            return list(toks)
        #reverse the toks if right-to-left chaining
        if not left_to_right:
            toks = toks[-1::-1]
        #collapse all identities with lower-precedence operators
        for i in range(0, len(toks), 2):
            toks[i] = _collapse_identity(toks[i], lower_precedence)
        #collapse all self-identities at index >= 2
        for i in range(2, len(toks), 2):
            toks[i] = _collapse_identity(toks[i], operator_value_list)
        #construct the Lisp code
        exp = [toks[0]]
        for operator, operand in zip(*(iter(toks[1:]),)*2):
            if swap_order:
                exp = [[operator_dict[operator], operand, exp[0]]]
            else:
                exp = [[operator_dict[operator], exp[0], operand]]
        return exp
    token = previous_token + Optional(\
            ZeroOrMore( MatchFirst((Literal(x) for x in operator_key_list)) + previous_token))
    token.setParseAction(f)
    return token

class ExperimentalParser():
    def __init__(self):
        # <expression>
        self.expression = Forward()


        # <symbol>
        #
        # evaluates to itself as a string, with the escaped char unescaped
        self.reserved_symbols = set(['if','else','proc',
            'true','false','lambda','identity', 'let','add','sub','div',
            'mul','pow','neq','gte','lte', 'eq', 'gt', 'lt', 'and', 'or'])
        def process_symbol(s, loc, toks):
            tok = re.sub(r'\\(.)',r'\1', toks[0])
            if tok in self.reserved_symbols:
                raise ParseException(s, loc,
                    "Reserved word cannot be symbol: " + tok, self)
            return [tok]
        self.symbol = Regex(r'[a-zA-Z_][a-zA-Z_0-9]*')
        self.symbol.setParseAction(process_symbol)


        # <number>
        #
        # evaluates to a python float
        def process_number(s, loc, toks):
            return [float(toks[0])]
        self.number = Regex(r'(-?\d+\.?\d*)|(-?\d*\.?\d+)')
        self.number.setParseAction(process_number)


        # <integer>
        #
        # evaluates to a python integer
        def process_integer(s, loc, toks):
            return [int(toks[0])]
        self.integer = Regex(r'\d+')
        self.integer.setParseAction(process_integer)


        # <string>
        #
        # evaluates to a python string
        def process_string(s, loc, toks):
            s = toks[0]
            s = s[1:-1]
            s = s.replace(r'\n','\n')
            s = s.replace(r'\t','\t')
            s = s.replace(r'\f','\f')
            s = s.replace(r'\b','\b')
            s = s.replace(r'\r','\r')
            s = s.replace("\\\\", "\\")
            s = s.replace(r"\/", '/')
            s = s.replace(r'\"','"')
            octals = list(re.finditer(r'\\[0-7]{3}', s))
            octals.reverse()
            for match in octals:
                st = match.group()
                i = int(st[1])*64+int(st[2])*8+int(st[3])
                if i > 127:
                    raise ParseException(s, loc,
                            "Octal too large for ASCII character: " + st, self.string)
                c = chr(i)
                start = match.start()
                end = match.end()
                s = s[:start] + c + s[end:]
            return [s]
        self.string = Regex(r'"(?:[^"\\]|\\"|\\\\|\\/|\\r|\\b|\\n|\\t|\\f|\\[0-7]{3})*"')
        self.string.setParseAction(process_string)



        # <null>
        #
        # evaluates to a python None
        def process_null(s, loc, toks):
            return [None]
        self.null = Keyword('null')
        self.null.setParseAction(process_null)


        # <boolean>
        #
        # evaluates to a python boolean
        def process_boolean(s, loc, toks):
            if toks[0] == 'true':
                return [True]
            return False
        self.boolean = Keyword('true') | Keyword('false')
        self.boolean.setParseAction(process_boolean)



        # <json_value>
        #
        # forward declaration
        self.json_value = Forward()


        # <json_list>
        #
        # evaluates to a python list
        def process_json_list(s, loc, toks):
            return [list(toks)]
        self.json_list = Literal('[').suppress() + Optional(
                    self.json_value + OneOrMore(
                        Literal(',').suppress() + self.json_value
                    )
                ) + Literal(']').suppress()
        self.json_list.setParseAction(process_json_list)



        # <json_object>
        #
        # evaluates to a python dict
        def process_json_object(s, loc, toks):
            return dict(zip(*(iter(toks),)*2))
        self.json_object = Literal('{').suppress() + Optional(
                    self.string + Literal(':').suppress() + self.json_value + ZeroOrMore(
                        Literal(',').suppress() + self.string +
                        Literal(':').suppress() + self.json_value
                    )
                ) + Literal('}').suppress()
        self.json_object.setParseAction(process_json_object)



        # <json_value>
        #
        # evaluates to a native json value
        def process_json_value(s, loc, toks):
            return list(toks)
        self.json_value << (self.string | self.number | self.boolean |
                self.null | self.json_list | self.json_object)
        self.json_value.setParseAction(process_json_value)


        # <value>
        #
        # evalues to something of the form {"type": "type_name", "value":<json_value>}
        #
        # forbid type_name in ('boolean', 'number') to preserve bijection
        def process_value(s, loc, toks):
            if toks[0] in ('number', 'boolean'):
                raise ParseException(s, loc,
                    "Not allowed to construct a " + toks[0] + " value. " +
                    "use a built-in primitive instead", self)
            return {"type": toks[0], "value": toks[1]}
        self.value = self.symbol + Literal('<').suppress() + self.json_value + Literal('>').suppress()
        self.value.setParseAction(process_value)


        # <number_literal>
        #
        # evalutes to a literal number value: {"type":"number", "value":s}
        def process_number_literal(s, loc, toks):
            return [{'type':'number', 'value':float(toks[0])}]
        self.number_literal = MatchFirst([self.number])
        self.number_literal.setParseAction(process_number_literal)



        # <boolean_literal>
        #
        # evalutes to a literal boolean value: {"type":"boolean", "value":s}
        def process_boolean_literal(s, loc, toks):
            return [{'type':'boolean', 'value':toks[0]}]
        self.boolean_literal = MatchFirst([self.boolean])
        self.boolean_literal.setParseAction(process_boolean_literal)



        # <literal>
        #
        # evaluates a json data type
        self.literal = self.boolean_literal | self.number_literal | self.value


        # <symbol_args>
        #
        # evaluates to a list: [<expression>*]
        def process_symbol_args(s, loc, toks):
            return [list(toks)]
        self.symbol_args = Literal("(").suppress() + (
                    Optional(self.symbol +  ZeroOrMore(Literal(",").suppress() + self.symbol))
                ) + Literal(")").suppress()
        self.symbol_args.setParseAction(process_symbol_args) 


        # <expression_args>
        #
        # evaluates to a list: [<expression>*]
        def process_expression_args(s, loc, toks):
            return [list(toks)]
        self.expression_args = Literal("(").suppress() + (
                    Optional(self.expression +  ZeroOrMore(Literal(",").suppress() + self.expression))
                ) + Literal(")").suppress()
        self.expression_args.setParseAction(process_expression_args) 


        # <assignments>
        #
        # evaluates to a list of [[<expression>,<expression>]*]
        def process_assignments(s, loc, toks):
            output = []
            for i in range(len(toks)/2):
                output.append(toks[2*i:2*(i+1)])
            return [output]
        self.assignments = OneOrMore(self.symbol + Literal("=").suppress() + self.expression)
        self.assignments.setParseAction(process_assignments)



        # <optional_let>
        #
        # evaluates to a list of ['let', <assignments>, <expression>]
        # or just <expression>
        def process_optional_let(s, loc, toks):
            if len(toks) == 1:
                if isinstance(toks[0], (list, tuple)) and toks[0][0] == 'let':
                    raise ParseException(s, loc,
                        "New scope is not allowed here", self)
                return list(toks)
            return [['let',toks[0],toks[1]]]
        self.optional_let = Optional(self.assignments) + self.expression
        self.optional_let.setParseAction(process_optional_let)


        # <identity>
        #
        # evaluates to ["identity", <expression>]
        def process_identity(s, loc, toks):
            return [["identity", toks[0]]] 
        self.identity = Literal("(").suppress() + self.expression + Literal(")")
        self.identity.setParseAction(process_identity)


        # <if_else>
        #
        # evaluates to ["if", <expression>, <expression>, <expression>]
        def process_if_else(s, loc, toks):
            return [["if", toks[0], toks[1], toks[2]]]
        self.if_else = Keyword("if").suppress() + Literal("(").suppress() +\
                self.optional_let + Literal(")").suppress() + Literal("{").suppress() +\
                self.optional_let + Literal("}").suppress() +\
                Keyword("else").suppress() + Literal("{").suppress() +\
                self.optional_let + Literal("}").suppress()
        self.if_else.setParseAction(process_if_else)


        # <proc>
        #
        # evaluates to ['lambda', <symbol_args>, <expression>]
        def process_proc(s, loc, toks):
            return [['lambda',toks[0], toks[1]]]
        self.proc = Keyword("proc").suppress() + self.symbol_args +\
                Literal("{").suppress() + self.optional_let +\
                Literal("}").suppress()
        self.proc.setParseAction(process_proc)


        # <let>
        #
        # evaluates to ['let', <assignments>, <expression>]
        def process_let(s, loc, toks):
            return [['let',toks[0],toks[1]]]
        self.let = Literal("{").suppress() + self.assignments + self.expression + Literal("}")
        self.let.setParseAction(process_let)


        # <non_fn_expression>
        #
        # evaluates to itself
        def process_non_fn_expression(s, loc, toks):
            return list(toks)
        self.non_fn_expression = (
                self.identity |
                self.proc |
                self.if_else |
                self.let |
                self.literal |
                self.symbol
                )


        # <fn_application>
        #
        # evaluates to [ .. [[<non_fn_expression>, *<args1>], *<args2>] .. , *<argsn>]
        # or <non_fn_expression> if no args provided
        def process_fn_application(s, loc, toks):
            if len(toks) == 1:
                return list(toks)
            #collapse possible infix identities
            exp = [_collapse_identity(toks[0], ('pow', 'add', 'sub', 'mul', 'div',
                'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or'))]
            for args in toks[1:]:
                exp = [exp+args]
            return exp
        self.fn_application = self.non_fn_expression + ZeroOrMore(self.expression_args)
        self.fn_application.setParseAction(process_fn_application)


        # <exponent>
        #
        # evaluates to ['power', .. ['power', <fn_app_n-1>, <fn_app_n>] ... , <fn_app_1>]
        # or <fn_application> if no exponents provided provided
        self.exponent = _make_infix_token(
                previous_token = self.fn_application,
                operator_map = (('**','pow'),),
                lower_precedence = ('add', 'sub', 'mul', 'div', 'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or'),
                left_to_right = False,
                swap_order = True,
                )


        # <mul_div>
        #
        # evaluates to [<op_n-1>, .. [<op_1>, <exponent_1>, <exponent_1>] ... , exponent_n>]
        # or <exponent> if no operators provided
        self.mul_div = _make_infix_token(
                previous_token = self.exponent,
                operator_map = (('*','mul'),('/','div')),
                lower_precedence = ('add', 'sub', 'eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or'),
                )



        # <add_sub>
        #
        # evaluates to [<op_n-1>, .. [<op_1>, <mul_div_1>, <mul_div_2>] ... , <mul_div_n>]
        # or <mul_div> if no operators provided
        self.add_sub = _make_infix_token(
                previous_token = self.mul_div,    
                operator_map = (('+','add'),('-','sub')),
                lower_precedence = ('eq', 'neq', 'lte', 'gte', 'gt', 'lt', 'and', 'or'),
                )


        # <comparison>
        #
        # evaluates to [<op_n>, <add_sub_1>, <add_sub_2>, ... , <add_sub_n>]
        # or <add_sub> if no operation token
        self.comparison = _make_infix_token(
                previous_token = self.add_sub,
                operator_map = (('<=','lte'),('>=','gte'),('<','lt'),('>','gt')),
                lower_precedence = ('eq', 'neq', 'and', 'or'),
                )


        # <equality>
        #
        # evaluates to [<op_n>, <comparison_1>, <comparison_2>, ... , <comparison_n>]
        # or <comparison> if no operation token
        self.equality = _make_infix_token(
                previous_token = self.comparison,
                operator_map = (('==','eq'),('!=','neq')),
                lower_precedence = ('and', 'or'),
                )


        # <boolean_and>
        #
        # evaluates to [<op1>, .. [<op2>, <fn_app_n-1>, <fn_app_n>] ... , <fn_app_1>]
        # or <equality> if no exponents provided provided
        self.boolean_and = _make_infix_token(
                previous_token = self.equality,
                operator_map = (('&&','and'),),
                lower_precedence = ('or'),
                )



        # <boolean_or>
        #
        # evaluates to [<op1>, .. [<op2>, <fn_app_n-1>, <fn_app_n>] ... , <fn_app_1>]
        # or <and> if no exponents provided provided
        self.boolean_or = _make_infix_token(
                previous_token = self.boolean_and,
                operator_map = (('||','or'),),
                lower_precedence = (),
                )


        # <expression>
        #
        # evaluates to itself
        def process_expression(s, loc, toks):
            return list(toks)
        self.expression << self.boolean_or
        self.expression.setParseAction(process_expression)


        # <directive_id>
        #
        # evaluates to itself
        def process_directive_id(s, loc, toks):
            return list(toks)
        self.directive_id = self.symbol | self.number
        self.directive_id.setParseAction(process_directive_id)


        # <assume>
        #
        # evaluates to a json instruction
        def process_assume(s, loc, toks):
            return [{
                "instruction" : "assume",
                "symbol" : toks[1],
                "expression" : toks[2]
                }]
        self.assume =  CaselessKeyword("assume") + self.symbol +\
                Literal("=").suppress() + self.expression
        self.assume.setParseAction(process_assume)


        # <predict>
        #
        # evaluates to a json instruction
        def process_predict(s, loc, toks):
            return [{
                "instruction" : "predict",
                "expression" : toks[1],
                }]
        self.predict =  CaselessKeyword("predict") + self.expression
        self.predict.setParseAction(process_predict)


        # <observe>
        #
        # evaluates to a json instruction
        def process_observe(s, loc, toks):
            return [{
                "instruction" : "observe",
                "expression" : toks[1],
                "value" : toks[2],
                }]
        self.observe =  CaselessKeyword("observe") + self.expression +\
                Literal("=").suppress() + self.literal
        self.observe.setParseAction(process_observe)


        # <forget>
        #
        # evaluates to a json instruction
        def process_forget(s, loc, toks):
            try:
                return [{
                    "instruction" : "forget",
                    "directive_id" : int(toks[1]),
                    }]
            except:
                return [{
                    "instruction" : "forget",
                    "label" : toks[1],
                    }]
        self.forget =  CaselessKeyword("forget") + self.directive_id
        self.forget.setParseAction(process_forget)


        # <sample>
        #
        # evaluates to a json instruction
        def process_sample(s, loc, toks):
            return [{
                "instruction" : "sample",
                "expression" : toks[1]
                }]
        self.sample =  CaselessKeyword("sample") + self.expression
        self.sample.setParseAction(process_sample)


        # <force>
        #
        # evaluates to a json instruction
        def process_force(s, loc, toks):
            return [{
                "instruction" : "force",
                "expression" : toks[1],
                "value" : toks[2]
                }]
        self.force =  CaselessKeyword("force") + self.expression +\
                Literal("=").suppress() + self.literal
        self.force.setParseAction(process_force)


        # <infer>
        #
        # evaluates to a json instruction
        def process_infer(s, loc, toks):
            return [{
                "instruction" : "infer",
                "iterations" : toks[1],
                "resample" : False,
                }]
        self.infer =  CaselessKeyword("infer") + self.integer
        self.infer.setParseAction(process_infer)


        # <named_directive>
        #
        # adds a "label" to the original directive
        def process_named_directive(s, loc, toks):
            toks[1].update({"label":toks[0]})
            return toks[1]
        self.named_directive =  self.symbol + Literal(":").suppress() +\
                (self.assume | self.predict | self.observe)
        self.named_directive.setParseAction(process_named_directive)


        # <unnamed_directive>
        #
        # evaluates to itself
        def process_unnamed_directive(s, loc, toks):
            return list(toks)
        self.unnamed_directive = (
                self.assume |
                self.predict |
                self.observe |
                self.forget |
                self.sample |
                self.force |
                self.infer
                )
        self.unnamed_directive.setParseAction(process_unnamed_directive)


        # <directive> (actually, it's an instruction)
        #
        # evaluates to itself
        def process_directive(s, loc, toks):
            return list(toks)
        self.directive = self.named_directive | self.unnamed_directive
        self.directive.setParseAction(process_directive)


        # <program>
        #
        # evaluates to itself
        def process_program(s, loc, toks):
            return list(toks)
        self.program = ZeroOrMore(self.directive)
        self.program.setParseAction(process_program)


    def parse_value(self, value):
        pass

    def parse_expression(self, expression):
        pass

    def parse_symbol(self, symbol):
        pass

    def parse_instruction(self, instruction):
        pass

    def split_program(self, program):
        pass

    def get_expression_index(self, expression_string, character_index):
        pass

    def get_text_range(self, expression_string, expression_index):
        pass

