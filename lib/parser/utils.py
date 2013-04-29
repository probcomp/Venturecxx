#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from pyparsing import Literal,CaselessLiteral,Regex,Word,Combine,Group,Optional,\
    ZeroOrMore,OneOrMore,Forward,nums,alphas,FollowedBy,Empty,ParseException,\
    Keyword, CaselessKeyword, MatchFirst
import re



# <symbol>
#
# evaluates to itself as a string
def symbol_token(reserved_symbols=set()):
    symbol = Regex(r'[a-zA-Z_][a-zA-Z_0-9]*')
    def process_symbol(s, loc, toks):
        tok = re.sub(r'\\(.)',r'\1', toks[0])
        if tok in reserved_symbols:
            raise ParseException(s, loc,
                "Reserved word cannot be symbol: " + tok, symbol)
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
        if toks[0] == 'true':
            return [True]
        return [False]
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
    return t

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
    boolean_literal = MatchFirst([boolean_token])
    boolean_literal.setParseAction(process_boolean_literal)
    return boolean_literal

# <literal>
#
# evaluates a json data type
def literal_token():
    return boolean_literal_token() | number_literal_token() | value_token()

# convert ParseException into VentureException
def apply_parser(element, string):
    try:
        return element.parseString(string)
    except ParseException as e:
        raise VentureException('text_parse',
                e.message, index=e.loc)
