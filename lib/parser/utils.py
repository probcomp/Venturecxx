#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst, ParseResults, White
import re
import json

from venture.exception import VentureException

def lw(thingy):
    # location_wrapper (or lw for short)
    # shortcut for chomping the leading whitespace
    # and augmenting the return value with a set
    # of text locations. "Thingy" is supposed to
    # be a ParserElement that returns a single
    # string at toks[0]
    x = Optional(White()).suppress() + MatchFirst([thingy]).leaveWhitespace()
    def process_x_token(s, loc, toks):
        if isinstance(toks[0], basestring):
            return [{'loc':[loc, loc+len(toks[0])-1], "value":toks[0]}]
        raise VentureException('fatal', 'The lw wrapper only accepts string-valued'
                "tokens. Got: " + toks[0])
    x.setParseAction(process_x_token)
    return MatchFirst([x])

def combine_locs(l):
    # combines the text-index locations of the given parsed tokens
    # into a single set
    mins = (a['loc'][0] for a in l)
    maxes = (a['loc'][1] for a in l)
    return [min(mins), max(maxes)]

# <symbol>
#
# evaluates to itself as a string
def symbol_token(blacklist_symbols=[], whitelist_symbols=[], symbol_map={}):
    regex = Regex(r'[a-zA-Z_][a-zA-Z_0-9]*')
    whitelist_toks = [Keyword(x) for x in whitelist_symbols]
    symbol = lw(MatchFirst([regex] + whitelist_toks))
    def process_symbol(s, loc, toks):
        tok = toks[0]['value']
        if tok in blacklist_symbols:
            raise ParseException(s,loc,"Reserved word cannot be symbol: " + tok)
        if tok in symbol_map:
            tok = symbol_map[tok]
        return [{"loc":toks[0]['loc'], "value":tok}]
    symbol.setParseAction(process_symbol)
    return symbol

# <number>
#
# evaluates to a python float
def number_token():
    number = lw(Regex(r'(-?\d+\.?\d*)|(-?\d*\.?\d+)'))
    def process_number(s, loc, toks):
        return [{"loc":toks[0]['loc'], "value":float(toks[0]['value'])}]
    number.setParseAction(process_number)
    return number

# <integer>
#
# evaluates to a python integer
def integer_token():
    integer = lw(Regex(r'\d+'))
    def process_integer(s, loc, toks):
        return [{"loc":toks[0]['loc'], "value":int(toks[0]['value'])}]
    integer.setParseAction(process_integer)
    return integer

# <string>
#
# evaluates to a python string
def string_token():
    # string = lw(Regex(r'"(?:[^"\\]|\\"|\\\\|\\/|\\r|\\b|\\n|\\t|\\f|\\[0-7]{3})*"'))
    # match more strings to produce helpful error message
    string = lw(Regex(r'"(?:[^"\\]|\\.)*"'))
    def process_string(s, loc, toks):
        s = toks[0]['value']
        s = s[1:-1]
        s = s.replace(r'\n','\n')
        s = s.replace(r'\t','\t')
        s = s.replace(r'\f','\f')
        s = s.replace(r'\b','\b')
        s = s.replace(r'\r','\r')
        s = s.replace(r"\/", '/')
        s = s.replace(r'\"','"')
        octals = list(re.finditer(r'\\[0-7]{3}', s))
        octals.reverse()
        for match in octals:
            st = match.group()
            i = int(st[1])*64+int(st[2])*8+int(st[3])
            if i > 127:
                raise VentureException("text_parse",
                        "Octal too large for ASCII character: " + st, text_index=toks[0]['loc'])
            c = chr(i)
            start = match.start()
            end = match.end()
            s = s[:start] + c + s[end:]
        tmp = []
        i = 0
        while i < len(s):
            if s[i] == '\\':
                if i == len(s) or s[i+1] != '\\':
                    raise VentureException("text_parse",
                            "Invalid escape sequence within string.", text_index=toks[0]['loc'])
                tmp.append('\\')
                i += 2
            else:
                tmp.append(s[i])
                i += 1
        s = ''.join(tmp)
        return [{"loc":toks[0]['loc'], "value":s}]
    string.setParseAction(process_string)
    return string

# <null>
#
# evaluates to a python None
def null_token():
    def process_null(s, loc, toks):
        return [{"loc":toks[0]['loc'], "value":None}]
    null = lw(Keyword('null'))
    null.setParseAction(process_null)
    return null

# <boolean>
#
# evaluates to a python boolean
def boolean_token():
    def process_boolean(s, loc, toks):
        n = toks[0]['value'] == 'true'
        return [{"loc":toks[0]['loc'], "value":n}]
    boolean = lw(Keyword('true') | Keyword('false'))
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
    json_list = lw(Literal('[')) + Optional(
                json_value + ZeroOrMore(
                    lw(Literal(',')) + json_value
                )
            ) + lw(Literal(']'))
    def process_json_list(s, loc, toks):
        v = [x['value'] for x in toks[1:-1:2]]
        l = combine_locs(toks)
        return [{"loc":l, "value":v}]
    json_list.setParseAction(process_json_list)

    #json_object
    json_object = lw(Literal('{')) + Optional(
                string + lw(Literal(':')) + json_value + ZeroOrMore(
                    lw(Literal(',')) + string +
                    lw(Literal(':')) + json_value
                )
            ) + lw(Literal('}'))
    def process_json_object(s, loc, toks):
        v = dict(zip(*(iter(x['value'] for x in toks[1:-1:2]),)*2))
        l = combine_locs(toks)
        return [{"loc":l, "value":v}]
    json_object.setParseAction(process_json_object)

    #json_value
    json_value << (string | number | boolean |
            null | json_list | json_object)
    def process_json_value(s, loc, toks):
        return [toks[0]]
    json_value.setParseAction(process_json_value)

    return json_value

# <value>
#
# evalues to something of the form {"type": "type_name", "value":<json_value>}
#
# forbid type_name in ('boolean', 'number') to preserve bijection
def value_token():
    value = symbol_token() + lw(Literal('<')) + json_value_token() + lw(Literal('>'))
    def process_value(s, loc, toks):
        if toks[0]['value'] in ('number', 'boolean'):
            raise ParseException("text_parse",
                "Not allowed to construct a " + toks[0]['value'] + " value. " +
                "use a built-in primitive instead", text_index=[loc,loc])
        v = {"type": toks[0]['value'], "value": toks[2]['value']}
        l = combine_locs(toks)
        return [{"loc":l, "value":v}]
    value.setParseAction(process_value)
    return value

# <number_literal>
#
# evalutes to a literal number value: {"type":"number", "value":s}
def number_literal_token():
    def process_number_literal(s, loc, toks):
        v = {'type':'number', 'value':float(toks[0]['value'])}
        l = toks[0]['loc']
        return [{"loc":l, "value":v}]
    number_literal = MatchFirst([number_token()])
    number_literal.setParseAction(process_number_literal)
    return number_literal

# <boolean_literal>
#
# evalutes to a literal boolean value: {"type":"boolean", "value":s}
def boolean_literal_token():
    def process_boolean_literal(s, loc, toks):
        v = {'type':'boolean', 'value':toks[0]['value']}
        l = toks[0]['loc']
        return [{"loc":l, "value":v}]
    boolean_literal = MatchFirst([boolean_token()])
    boolean_literal.setParseAction(process_boolean_literal)
    return boolean_literal

# <literal>
#
# evaluates a json data type
def literal_token():
    literal = boolean_literal_token() | number_literal_token() | value_token()
    def process_literal(s, loc, toks):
        return [toks[0]]
    literal.setParseAction(process_literal)
    return literal

# convert ParseException into VentureException
def apply_parser(element, string):
    if not isinstance(string, basestring):
        raise VentureException('fatal',
                'Parser only accepts strings')
    try:
        return list(element.parseString(string, parseAll=True))
    except ParseException as e:
        raise VentureException('text_parse',
                str(e), text_index=[e.loc,e.loc])

def value_to_string(v):
    if isinstance(v, dict):
        if (not 'type' in v) or (not 'value' in v):
            raise VentureException('fatal',
                    'Value should take the form {"type":<type>, "value":<value>}.')
        if v['type'] == "boolean":
            if v['value'] == True:
                return 'true'
            if v['value'] == False:
                return 'true'
            raise VentureException('fatal',
                    'Invalid boolean value')
        if v['type'] == "number":
            if not isinstance(v['value'], (int, float)):
                raise VentureException('fatal',
                        'Invalid number value')
            return "{}".format(v['value'])
        try:
            return "{}<{}>".format(
                    v['type'],
                    json.dumps(v['value']))
        except:
            raise VentureException('fatal',
                    'Invalid value -- could not convert to json string')
    if isinstance(v, bool):
        if v:
            return "true"
        return "false"
    if isinstance(v, (int, float)):
        return "{}".format(v)
    if isinstance(v, basestring):
        return v
    raise VentureException('fatal',
            'Value must be a dict, boolean, number, or pre-formatted string')

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

def get_program_string_fragments(s,locs):
    output = []
    for loc in locs:
        output.append(s[loc[0]:loc[1]+1])
    return output

def get_instruction_string_fragments(s,locs):
    output = {}
    for key, loc in locs.items():
        output[key] = s[loc[0]:loc[1]+1]
    return output

def get_text_index(parse_tree, expression_index):
    """parse-tree-index to text index"""
    if len(expression_index) == 0:
        return parse_tree['loc']
    tmp = parse_tree
    try:
        for i in expression_index[:-1]:
            tmp = tmp['value'][i]
        x = tmp['value'][expression_index[-1]]['loc']
        if x == None:
            raise VentureException("no_text_index", "Expression index does"\
                " not have a corresponding text index" + str(e.message))
        return x
    except Exception as e:
        raise VentureException("no_text_index", "Expression index is invalid: " + str(e.message))

def get_expression_index(parse_tree, text_index):
    """text index to expression-index, the parse_tree
    is supposed to be the parse tree of an exception"""
    d = {}
    def unpack(l, prefix=[]):
        for loc in range(l['loc'][0], l['loc'][1]+1):
            if loc in d:
                d[loc].append(prefix)
            else:
                d[loc] = [prefix]
        if isinstance(l['value'], (list, tuple, ParseResults)):
            for index, elem in enumerate(l['value']):
                unpack(elem, prefix + [index])
    unpack(parse_tree)
    if not text_index in d:
        raise VentureException("no_expression_index", "Text index {} does not"
                "correspond to an expression index".format(text_index))
    #preference for the most specific (longest) expression index
    exps = d[text_index]
    output = None
    for e in exps:
        if output == None or len(e) > len(output):
            output = e
    return output

def inst(keyword, instruction):
    k = lw(CaselessKeyword(keyword))
    def process_k(s, loc, toks):
        return [{'loc':toks[0]['loc'], "value":instruction}]
    k.setParseAction(process_k)
    return k


def init_instructions(value, symbol, expression):

    # assume
    assume = inst('assume', 'assume') + symbol + lw(Literal("=")) + expression
    def process_assume(s, loc, toks):
        v = {
                'instruction': toks[0],
                'symbol': toks[1],
                'expression': toks[3],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    assume.setParseAction(process_assume)

    # labeled assume
    labeled_assume = symbol + lw(Literal(":")) + inst('assume', 'labeled_assume')\
            + symbol + lw(Literal("=")) + expression
    def process_labeled_assume(s, loc, toks):
        v = {
                'instruction': toks[2],
                'symbol': toks[3],
                'expression': toks[5],
                'label': toks[0],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    labeled_assume.setParseAction(process_labeled_assume)

    # observe
    observe = inst('observe', 'observe') + expression\
            + lw(Literal("=")) + value
    def process_observe(s, loc, toks):
        v = {
                'instruction': toks[0],
                'value': toks[3],
                'expression': toks[1],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    observe.setParseAction(process_observe)

    # labeled observe
    labeled_observe = symbol + lw(Literal(":"))\
            + inst('observe','labeled_observe') + expression\
            + lw(Literal("=")) + value
    def process_labeled_observe(s, loc, toks):
        v = {
                'instruction': toks[2],
                'value': toks[5],
                'expression': toks[3],
                'label': toks[0],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    labeled_observe.setParseAction(process_labeled_observe)

    # predict 
    predict = inst('predict', 'predict') + expression
    def process_predict(s, loc, toks):
        v = {
                'instruction': toks[0],
                'expression': toks[1],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    predict.setParseAction(process_predict)

    # labeled predict 
    labeled_predict = symbol + lw(Literal(":"))\
            + inst('predict', 'labeled_predict') + expression
    def process_labeled_predict(s, loc, toks):
        v = {
                'instruction': toks[2],
                'expression': toks[3],
                'label': toks[0],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    labeled_predict.setParseAction(process_labeled_predict)


    # forget 
    forget = inst('forget', 'forget') + integer_token()
    def process_forget(s, loc, toks):
        v = {
                'instruction': toks[0],
                'directive_id': toks[1],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    forget.setParseAction(process_forget)

    # labeled forget 
    labeled_forget = inst('forget', 'labeled_forget') + symbol
    def process_labeled_forget(s, loc, toks):
        v = {
                'instruction': toks[0],
                'label': toks[1],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    labeled_forget.setParseAction(process_labeled_forget)


    # force
    force = inst('force','force') + expression\
            + lw(Literal("=")) + value
    def process_force(s, loc, toks):
        v = {
                'instruction': toks[0],
                'value': toks[3],
                'expression': toks[1],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    force.setParseAction(process_force)

    # sample 
    sample = inst('sample','sample') + expression
    def process_sample(s, loc, toks):
        v = {
                'instruction': toks[0],
                'expression': toks[1],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    sample.setParseAction(process_sample)

    # infer 
    infer = inst('infer', 'infer') + integer_token()\
            + Optional(boolean_token())
    def process_infer(s, loc, toks):
        if len(toks) == 3:
            resample = toks[2]
        else:
            resample = {'loc':toks[0]['loc'], "value":False}
        v = {
                'instruction': toks[0],
                'iterations': toks[1],
                "resample" : resample,
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    infer.setParseAction(process_infer)

    # clear 
    clear= inst('clear', 'clear')
    def process_clear(s, loc, toks):
        v = {
                'instruction': toks[0],
                }
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    clear.setParseAction(process_clear)

    instruction = assume | labeled_assume | predict | labeled_predict | observe\
            | labeled_observe | forget | labeled_forget | sample | force\
            | infer | clear
    def process_instruction(s, loc, toks):
        return [toks[0]]
    instruction.setParseAction(process_instruction)
    instruction = instruction

    program = OneOrMore(instruction)
    def process_program(s, loc, toks):
        v = list(toks)
        l = combine_locs(toks)
        return [{'loc':l, "value":v}]
    program.setParseAction(process_program)
    program = program

    return instruction, program
