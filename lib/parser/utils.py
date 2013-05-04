#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst, ParseResults
import re

from venture.exception import VentureException


# <symbol>
#
# evaluates to itself as a string
def symbol_token(blacklist_symbols=[], whitelist_symbols=[], symbol_map={}):
    regex = Regex(r'[a-zA-Z_][a-zA-Z_0-9]*')
    whitelist_toks = [Keyword(x) for x in whitelist_symbols]
    symbol = MatchFirst([regex] + whitelist_toks)
    def process_symbol(s, loc, toks):
        tok = toks[0][:]
        if tok in blacklist_symbols:
            raise ParseException(s, loc,
                "Reserved word cannot be symbol: " + tok, symbol)
        if tok in symbol_map:
            tok = symbol_map[tok]
        return [tok]
    symbol.setParseAction(process_symbol)
    return symbol

# <number>
#
# evaluates to a python float
def number_token():
    number = Regex(r'(-?\d+\.?\d*)|(-?\d*\.?\d+)')
    def process_number(s, loc, toks):
        return [float(toks[0])]
    number.setParseAction(process_number)
    return number

# <integer>
#
# evaluates to a python integer
def integer_token():
    integer = Regex(r'\d+')
    def process_integer(s, loc, toks):
        return [int(toks[0])]
    integer.setParseAction(process_integer)
    return integer

# <string>
#
# evaluates to a python string
def string_token():
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
        return [s]
    string.setParseAction(process_string)
    return string

# <null>
#
# evaluates to a python None
def null_token():
    def process_null(s, loc, toks):
        return [None]
    null = Keyword('null')
    null.setParseAction(process_null)
    return null

# <boolean>
#
# evaluates to a python boolean
def boolean_token():
    def process_boolean(s, loc, toks):
        return [toks[0] == 'true']
    boolean = Keyword('true') | Keyword('false')
    boolean.setParseAction(process_boolean)
    return boolean

# <json_value>
#
# evaluates to a native json value
def json_value_token():
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
        return list(toks)
    json_value.setParseAction(process_json_value)

    return json_value

# <value>
#
# evalues to something of the form {"type": "type_name", "value":<json_value>}
#
# forbid type_name in ('boolean', 'number') to preserve bijection
def value_token():
    value = symbol_token() + Literal('<').suppress() + json_value_token() + Literal('>').suppress()
    def process_value(s, loc, toks):
        if toks[0] in ('number', 'boolean'):
            raise ParseException(s, loc,
                "Not allowed to construct a " + toks[0] + " value. " +
                "use a built-in primitive instead", value)
        return [{"type": toks[0], "value": toks[1]}]
    value.setParseAction(process_value)
    return value

# <number_literal>
#
# evalutes to a literal number value: {"type":"number", "value":s}
def number_literal_token():
    def process_number_literal(s, loc, toks):
        return [{'type':'number', 'value':float(toks[0])}]
    number_literal = MatchFirst([number_token()])
    number_literal.setParseAction(process_number_literal)
    return number_literal

# <boolean_literal>
#
# evalutes to a literal boolean value: {"type":"boolean", "value":s}
def boolean_literal_token():
    def process_boolean_literal(s, loc, toks):
        return [{'type':'boolean', 'value':toks[0]}]
    boolean_literal = MatchFirst([boolean_token()])
    boolean_literal.setParseAction(process_boolean_literal)
    return boolean_literal

# <literal>
#
# evaluates a json data type
def literal_token():
    literal = boolean_literal_token() | number_literal_token() | value_token()
    def process_literal(s, loc, toks):
        return list(toks)
    literal.setParseAction(process_literal)
    return literal

def location_wrapper(thingy):
    # shortcut for chomping the leading whitespace
    # (workaround for MatchFirst returning the wrong
    # loc in the presence of leading whitespace)
    chomp = ZeroOrMore(Literal(' ')).suppress() 
    x = chomp + MatchFirst([thingy])
    def process_x_token(s, loc, toks):
        return [{'loc':loc, "value":toks[0]}]
    x.setParseAction(process_x_token)
    return x

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

def _unpack(l):
    if isinstance(l['value'], (list, tuple, ParseResults)):
        return [_unpack(x) for x in l['value']]
    return l['value']

def simplify_expression_parse_tree(parse_tree):
    return _unpack(parse_tree)

def simplify_instruction_parse_tree(parse_tree):
    output = {}
    for key, value in parse_tree['value'].items():
        output[key] = _unpack(value)
    return output

def simplify_program_parse_tree(parse_tree):
    return [simplify_instruction_parse_tree(x) for x in parse_tree['value']]

def split_instruction_parse_tree(parse_tree):
    output = {}
    for key, value in parse_tree['value'].items():
        output[key] = value['loc']
    return output

def split_program_parse_tree(parse_tree):
    return [x['loc'] for x in parse_tree['value']]

def get_string_fragments(s,locs):
    output = []
    tmp = s
    for loc in locs[::-1]:
        output.insert(0, tmp[loc:])
        tmp = tmp[:loc]
    return output

def get_text_index(parse_tree, expression_index):
    """parse-tree-index to text index"""
    if len(expression_index) == 0:
        return parse_tree['loc']
    tmp = parse_tree
    try:
        for i in expression_index[:-1]:
            tmp = tmp['value'][i]
        return tmp['value'][expression_index[-1]]['loc']
    except Exception as e:
        raise VentureException("fatal", "Expression index not found: " + str(e.message))

def get_expression_index(parse_tree, text_index):
    """text index to expression-index, the parse_tree
    is supposed to be the parse tree of an exception"""
    d = {}
    def unpack(l, prefix=[]):
        loc = l['loc']
        if loc in d:
            d[loc].append(prefix)
        else:
            d[loc] = [prefix]
        if isinstance(l['value'], (list, tuple, ParseResults)):
            for index, elem in enumerate(l['value']):
                unpack(elem, prefix + [index])
    unpack(parse_tree)
    s = sorted(d.items(), key=lambda x: x[0])
    i = 0
    while i + 1 < len(s) and s[i+1][0] <= text_index:
        i += 1
    if len(s) == 0:
        raise VentureException("fatal", "No parse tree available")
    # a click before the start of the expression corresponds to the entire expression
    if text_index < s[i][0]:
        return []
    #preference for the most specific (longest) expression index
    exps = s[i][1]
    output = None
    for e in exps:
        if output == None or len(e) > len(output):
            output = e
    return output

def inst(keyword, instruction):
    k = CaselessKeyword(keyword)
    def process_k(s, loc, toks):
        return {'loc':loc, "value":instruction}
    k.setParseAction(process_k)
    return k


def init_instructions(value, symbol, expression):
    """ value, symbol, and expression are expected to already
    be wrapped in a location_wrapper token """
    # assume
    assume = inst('assume', 'assume') + symbol + Literal("=").suppress() + expression
    def process_assume(s, loc, toks):
        return [{
                'instruction': toks[0],
                'symbol': toks[1],
                'expression': toks[2],
                }]
    assume.setParseAction(process_assume)

    # labeled assume
    labeled_assume = symbol + Literal(":").suppress() + inst('assume', 'labeled_assume')\
            + symbol + Literal("=").suppress() + expression
    def process_labeled_assume(s, loc, toks):
        return [{
                'instruction': toks[1],
                'symbol': toks[2],
                'expression': toks[3],
                'label': toks[0],
                }]
    labeled_assume.setParseAction(process_labeled_assume)

    # observe
    observe = inst('observe', 'observe') + expression\
            + Literal("=").suppress() + value
    def process_observe(s, loc, toks):
        return [{
                'instruction': toks[0],
                'value': toks[2],
                'expression': toks[1],
                }]
    observe.setParseAction(process_observe)

    # labeled observe
    labeled_observe = symbol + Literal(":").suppress()\
            + inst('observe','labeled_observe') + expression\
            + Literal("=").suppress() + value
    def process_labeled_observe(s, loc, toks):
        return [{
                'instruction': toks[1],
                'value': toks[3],
                'expression': toks[2],
                'label': toks[0],
                }]
    labeled_observe.setParseAction(process_labeled_observe)

    # predict 
    predict = inst('predict', 'predict') + expression
    def process_predict(s, loc, toks):
        return [{
                'instruction': toks[0],
                'expression': toks[1],
                }]
    predict.setParseAction(process_predict)

    # labeled predict 
    labeled_predict = symbol + Literal(":").suppress()\
            + inst('predict', 'labeled_predict') + expression
    def process_labeled_predict(s, loc, toks):
        return [{
                'instruction': toks[1],
                'expression': toks[2],
                'label': toks[0],
                }]
    labeled_predict.setParseAction(process_labeled_predict)


    # forget 
    forget = inst('forget', 'forget') + location_wrapper(integer_token())
    def process_forget(s, loc, toks):
        return [{
                'instruction': toks[0],
                'directive_id': toks[1],
                }]
    forget.setParseAction(process_forget)

    # labeled forget 
    labeled_forget = inst('forget', 'labeled_forget') + symbol
    def process_labeled_forget(s, loc, toks):
        return [{
                'instruction': toks[0],
                'label': toks[1],
                }]
    labeled_forget.setParseAction(process_labeled_forget)


    # force
    force = inst('force','force') + expression\
            + Literal("=").suppress() + value
    def process_force(s, loc, toks):
        return [{
                'instruction': toks[0],
                'value': toks[2],
                'expression': toks[1],
                }]
    force.setParseAction(process_force)

    # sample 
    sample = inst('sample','sample') + expression
    def process_sample(s, loc, toks):
        return [{
                'instruction': toks[0],
                'expression': toks[1],
                }]
    sample.setParseAction(process_sample)

    # infer 
    infer = inst('infer', 'infer') + location_wrapper(integer_token())\
            + Optional(boolean_token())
    def process_infer(s, loc, toks):
        if len(toks) == 3:
            resample = toks[2]
        else:
            resample = {'loc':toks[0]['loc'], "value":False}
        return [{
                'instruction': toks[0],
                'iterations': toks[1],
                "resample" : resample,
                }]
    infer.setParseAction(process_infer)

    instruction = assume | labeled_assume | predict | labeled_predict | observe\
            | labeled_observe | forget | labeled_forget | sample | force\
            | infer
    def process_instruction(s, loc, toks):
        return list(toks)
    instruction.setParseAction(process_instruction)
    instruction = location_wrapper(instruction)

    program = OneOrMore(instruction)
    def process_program(s, loc, toks):
        return [list(toks)]
    program.setParseAction(process_program)
    program = location_wrapper(program)

    return instruction, program
