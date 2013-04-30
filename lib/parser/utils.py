#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re

from venture.exception import VentureException


def push_stack(stack, loc):
    if isinstance(stack, (list, tuple)):
        stack.append({
            "index":loc,
            "children":[],
            })
        print "stack append:", stack

def nest_stack(stack, loc, n):
    if isinstance(stack, (list, tuple)) and n > 0:
        print "nest_stack:", n
        children = stack[-n:]
        for i in range(n):
            stack.pop()
        stack.append({
            "index":loc,
            "children":children,
            })
        print "finish:", stack

# shortcut for chomping the leading whitespace
# (workaround for MatchFirst returning the wrong
# loc in the presence of leading whitespace)
chomp = ZeroOrMore(Literal(' ')).suppress() 

# <symbol>
#
# evaluates to itself as a string
def symbol_token(stack=None, blacklist_symbols=[], whitelist_symbols=[], symbol_map={}):
    regex = Regex(r'[a-zA-Z_][a-zA-Z_0-9]*')
    whitelist_toks = [Keyword(x) for x in whitelist_symbols]
    symbol = chomp + MatchFirst([regex] + whitelist_toks)
    def process_symbol(s, loc, toks):
        tok = toks[0][:]
        if tok in blacklist_symbols:
            raise ParseException(s, loc,
                "Reserved word cannot be symbol: " + tok, symbol)
        if tok in symbol_map:
            tok = symbol_map[tok]
        print "symbol", toks
        push_stack(stack, loc)
        return [tok]
    symbol.setParseAction(process_symbol)
    return symbol

# <number>
#
# evaluates to a python float
def number_token(stack=None):
    number = Regex(r'(-?\d+\.?\d*)|(-?\d*\.?\d+)')
    def process_number(s, loc, toks):
        print 'token', toks
        push_stack(stack, loc)
        return [float(toks[0])]
    number.setParseAction(process_number)
    return number

# <integer>
#
# evaluates to a python integer
def integer_token(stack=None):
    integer = Regex(r'\d+')
    def process_integer(s, loc, toks):
        print 'integer', toks
        push_stack(stack, loc)
        return [int(toks[0])]
    integer.setParseAction(process_integer)
    return integer

# <string>
#
# evaluates to a python string
def string_token(stack=None):
    string = Regex(r'"(?:[^"\\]|\\"|\\\\|\\/|\\r|\\b|\\n|\\t|\\f|\\[0-7]{3})*"')
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
                        "Octal too large for ASCII character: " + st, string)
            c = chr(i)
            start = match.start()
            end = match.end()
            s = s[:start] + c + s[end:]
        print 'string', toks
        push_stack(stack, loc)
        return [s]
    string.setParseAction(process_string)
    return string

# <null>
#
# evaluates to a python None
def null_token(stack=None):
    def process_null(s, loc, toks):
        print 'null', toks
        push_stack(stack, loc)
        return [None]
    null = Keyword('null')
    null.setParseAction(process_null)
    return null

# <boolean>
#
# evaluates to a python boolean
def boolean_token(stack=None):
    def process_boolean(s, loc, toks):
        print 'boolean', toks
        push_stack(stack, loc)
        if toks[0] == 'true':
            return [True]
        return [False]
    boolean = Keyword('true') | Keyword('false')
    boolean.setParseAction(process_boolean)
    return boolean

# <json_value>
#
# evaluates to a native json value
def json_value_token(stack=None):
    json_value = Forward()

    string = string_token()
    number = number_token()
    null = null_token()
    boolean = boolean_token()

    #json_list
    json_list = Literal('[').suppress() + Optional(
                json_value + OneOrMore(
                    Literal(',').suppress() + json_value
                )
            ) + Literal(']').suppress()
    def process_json_list(s, loc, toks):
        return [list(toks)]
    json_list.setParseAction(process_json_list)

    #json_object
    json_object = Literal('{').suppress() + Optional(
                string + Literal(':').suppress() + json_value + ZeroOrMore(
                    Literal(',').suppress() + string +
                    Literal(':').suppress() + json_value
                )
            ) + Literal('}').suppress()
    def process_json_object(s, loc, toks):
        return [dict(zip(*(iter(toks),)*2))]
    json_object.setParseAction(process_json_object)

    #json_value
    json_value << (string | number | boolean |
            null | json_list | json_object)
    def process_json_value(s, loc, toks):
        print 'json_value', toks
        push_stack(stack, loc)
        return list(toks)
    json_value.setParseAction(process_json_value)

    return json_value

# <value>
#
# evalues to something of the form {"type": "type_name", "value":<json_value>}
#
# forbid type_name in ('boolean', 'number') to preserve bijection
def value_token(stack=None):
    value = symbol_token() + Literal('<').suppress() + json_value_token() + Literal('>').suppress()
    def process_value(s, loc, toks):
        if toks[0] in ('number', 'boolean'):
            raise ParseException(s, loc,
                "Not allowed to construct a " + toks[0] + " value. " +
                "use a built-in primitive instead", value)
        print 'value', toks
        push_stack(stack, loc)
        return [{"type": toks[0], "value": toks[1]}]
    value.setParseAction(process_value)
    return value

# <number_literal>
#
# evalutes to a literal number value: {"type":"number", "value":s}
def number_literal_token(stack=None):
    def process_number_literal(s, loc, toks):
        print 'number_literal', toks
        push_stack(stack, loc)
        return [{'type':'number', 'value':float(toks[0])}]
    number_literal = MatchFirst([number_token()])
    number_literal.setParseAction(process_number_literal)
    return number_literal

# <boolean_literal>
#
# evalutes to a literal boolean value: {"type":"boolean", "value":s}
def boolean_literal_token(stack=None):
    def process_boolean_literal(s, loc, toks):
        print 'boolean_literal', toks
        push_stack(stack, loc)
        return [{'type':'boolean', 'value':toks[0]}]
    boolean_literal = MatchFirst([boolean_token()])
    boolean_literal.setParseAction(process_boolean_literal)
    return boolean_literal

# <literal>
#
# evaluates a json data type
def literal_token(stack=None):
    return boolean_literal_token(stack) | number_literal_token(stack) | value_token(stack)

# convert ParseException into VentureException
def apply_parser(element, string):
    if not isinstance(string, basestring):
        raise VentureException('fatal',
                'Parser only accepts strings')
    try:
        return list(element.parseString(string))
    except ParseException as e:
        raise VentureException('text_parse',
                e.message, index=e.loc)


def get_text_index(stack, *args):
    """parse-tree-index to text index"""
    tmp = stack
    try:
        for i in args[:-1]:
            tmp = tmp[i]['children']
        return tmp[args[-1]]['index']
    except Exception as e:
        raise VentureException("fatal", "Expression index not found: " + e.message)

def get_parse_tree_index(root_list, index):
    """text index to parse-tree-index"""
    d = {}
    # root_list is basically a mapping from expression index
    # to text index. we first need to create the reverse map
    def unpack(l, prefix=[]):
        for index, elem in enumerate(l):
            text_index = elem['index']
            exp_index = prefix + [index]
            if text_index in d:
                d[text_index].append(exp_index)
            else:
                d[text_index] = [exp_index]
            unpack(elem['children'], exp_index)
    unpack(root_list)
    s = sorted(d.items(), key=lambda x: x[0])
    i = 0
    while i + 1 < len(s) and s[i+1][0] <= index:
        i += 1
    if len(s) == 0 or s[i][0] > index:
        raise VentureException("fatal", "No parse tree available")
    #preference for the most specific (longest) expression index
    exps = s[i][1]
    output = None
    for e in exps:
        if output == None or len(e) > len(output):
            output = e
    return output


def init_instructions(value, symbol, expression, stack=None):

    # assume
    assume = CaselessKeyword('assume').suppress() + symbol + Literal("=").suppress() + expression
    def process_assume(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'assume',
                'symbol': toks[0],
                'expression': toks[1],
                }]
    assume.setParseAction(process_assume)

    # labeled assume
    labeled_assume = symbol + Literal(":").suppress() + CaselessKeyword('assume').suppress()\
            + symbol + Literal("=").suppress() + expression
    def process_labeled_assume(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'labeled_assume',
                'symbol': toks[1],
                'expression': toks[2],
                'label': toks[0],
                }]
    labeled_assume.setParseAction(process_labeled_assume)

    # observe
    observe = CaselessKeyword('observe').suppress() + expression\
            + Literal("=").suppress() + value
    def process_observe(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'observe',
                'value': toks[1],
                'expression': toks[0],
                }]
    observe.setParseAction(process_observe)

    # labeled observe
    labeled_observe = symbol + Literal(":").suppress()\
            + CaselessKeyword('observe').suppress() + expression\
            + Literal("=").suppress() + value
    def process_labeled_observe(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'labeled_observe',
                'value': toks[2],
                'expression': toks[1],
                'label': toks[0],
                }]
    labeled_observe.setParseAction(process_labeled_observe)

    # predict 
    predict = CaselessKeyword('predict').suppress() + expression
    def process_predict(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'predict',
                'expression': toks[0],
                }]
    predict.setParseAction(process_predict)

    # labeled predict 
    labeled_predict = symbol + Literal(":").suppress()\
            + CaselessKeyword('predict').suppress() + expression
    def process_labeled_predict(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'labeled_predict',
                'expression': toks[1],
                'label': toks[0],
                }]
    labeled_predict.setParseAction(process_labeled_predict)


    # forget 
    forget = CaselessKeyword('forget').suppress() + integer_token(stack)
    def process_forget(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'forget',
                'directive_id': toks[0],
                }]
    forget.setParseAction(process_forget)

    # labeled forget 
    labeled_forget = CaselessKeyword('forget').suppress() + symbol
    def process_labeled_forget(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'labeled_forget',
                'label': toks[0],
                }]
    labeled_forget.setParseAction(process_labeled_forget)


    # force
    force = CaselessKeyword('force').suppress() + expression\
            + Literal("=").suppress() + value
    def process_force(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'force',
                'value': toks[1],
                'expression': toks[0],
                }]
    force.setParseAction(process_force)

    # sample 
    sample = CaselessKeyword('sample').suppress() + expression
    def process_sample(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return [{
                'instruction': 'sample',
                'expression': toks[0],
                }]
    sample.setParseAction(process_sample)

    # infer 
    infer = CaselessKeyword('infer').suppress() + integer_token(stack)\
            + Optional(boolean_token(stack))
    def process_infer(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        if len(toks) == 2:
            resmple = toks[1]
        else:
            resample = False
        return [{
                'instruction': 'infer',
                'iterations': toks[0],
                "resample" : resample,
                }]
    infer.setParseAction(process_infer)

    instruction = assume | labeled_assume | predict | labeled_predict | observe\
            | labeled_observe | forget | labeled_forget | sample | force\
            | infer
    def process_instruction(s, loc, toks):
        return list(toks)
    instruction.setParseAction(process_instruction)

    program = OneOrMore(instruction)
    def process_program(s, loc, toks):
        nest_stack(stack, loc, len(toks))
        return list(toks)
    program.setParseAction(process_program)

    return instruction, program
