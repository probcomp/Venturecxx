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

# Venture lexical scanner (`VentureScript', JavaScript-style notation).

import StringIO

import venture.plex as Plex

from venture.parser import ast
from venture.parser.venture_script import grammar

# XXX Automatically confirm we at least mention all tokens mentioned
# in the grammar.

'''
grep -o -E 'K_[A-Z0-9_]+' < grammar.y | sort -u | awk '
BEGIN {
    q = "'\''"
}
{
    sub("^K_", "", $1)
    printf("    %c%s%c: grammar.K_%s,\n", q, tolower($1), q, $1)
}
END {
    printf("    %ctrue%c: grammar.T_TRUE,\n", q, q);
    printf("    %cfalse%c: grammar.T_FALSE,\n", q, q);
}'
'''
keywords = {                    # XXX Use a perfect hash.
    'add': grammar.K_ADD,
    'and': grammar.K_AND,
    'assume': grammar.K_ASSUME,
    'define': grammar.K_DEFINE,
    'div': grammar.K_DIV,
    'else': grammar.K_ELSE,
    'eq': grammar.K_EQ,
    'ge': grammar.K_GE,
    'gt': grammar.K_GT,
    'force': grammar.K_FORCE,
    'if': grammar.K_IF,
    'infer': grammar.K_INFER,
    'lambda': grammar.K_LAMBDA,
    'le': grammar.K_LE,
    'let': grammar.K_LET,
    'letrec': grammar.K_LETREC,
    'load': grammar.K_LOAD,
    'lt': grammar.K_LT,
    'mul': grammar.K_MUL,
    'neq': grammar.K_NEQ,
    'observe': grammar.K_OBSERVE,
    'or': grammar.K_OR,
    'pow': grammar.K_POW,
    'predict': grammar.K_PREDICT,
    'proc': grammar.K_PROC,
    'sample': grammar.K_SAMPLE,
    'sub': grammar.K_SUB,
    'true': grammar.T_TRUE,
    'false': grammar.T_FALSE,
}
def scan_name(_scanner, text):
    return keywords.get(text) or keywords.get(text.lower()) or grammar.L_NAME

def scan_integer(scanner, text):
    scanner.produce(grammar.L_INTEGER, int(text, 10))

def scan_real(scanner, text):
    scanner.produce(grammar.L_REAL, float(text))

def scan_string(scanner, text):
    assert scanner.stringio is None
    scanner.stringio = StringIO.StringIO()
    scanner.string_start = scanner.cur_pos - len(text)
    scanner.begin('STRING')

def scan_string_text(scanner, text):
    assert scanner.stringio is not None
    scanner.stringio.write(text)

escapes = {
    '/':        '/',
    '\"':       '\"',
    '\\':       '\\',
    'b':        '\b',           # Backspace
    'f':        '\f',           # Form feed
    'n':        '\n',           # Line feed
    'r':        '\r',           # Carriage return
    't':        '\t',           # Horizontal tab
}
def scan_string_escape(scanner, text):
    assert scanner.stringio is not None
    assert text[0] == '\\'
    assert text[1] in escapes
    scanner.stringio.write(escapes[text[1]])

def scan_string_escerror(scanner, text):
    assert scanner.stringio is not None
    # XXX Report error.
    scanner.stringio.write('?error?')

def scan_string_octal(scanner, text):
    assert scanner.stringio is not None
    assert text[0] == '\\'
    n = int(text[1:], 8)
    # XXX Report error.
    scanner.stringio.write(chr(n) if n < 128 else '?error?')

def scan_string_end(scanner, text):
    assert scanner.stringio is not None
    assert text == '"'
    string = scanner.stringio.getvalue()
    scanner.stringio.close()
    scanner.stringio = None
    length = scanner.cur_pos - scanner.string_start
    scanner.string_start = None
    scanner.produce(grammar.L_STRING, string, length)
    scanner.begin('')

def scan_language(scanner, text):
    assert text.startswith('@{')
    assert scanner.current_language is None
    language = text[len('@{'):]
    if language not in scanner.languages:
        scanner.produce(-1)
    scanner.current_language = scanner.languages[language]()
    scanner.begin('LANGUAGE')

def scan_language_char(scanner, text):
    done, result = scanner.current_language(text)
    if done:
        del scanner.current_language
        scanner.current_language = None
        scanner.produce(grammar.L_LANGUAGE, result)
        scanner.begin('')

def scan_comment_open(scanner, _text):
    scanner.comment_level += 1
    scanner.begin('BLOCK_COMMENT')

def scan_comment_close(scanner, _text):
    assert scanner.comment_level > 0
    scanner.comment_level -= 1
    if scanner.comment_level == 0:
        scanner.begin('')

class Scanner(Plex.Scanner):
    line_comment = Plex.Str('//') + Plex.Rep(Plex.AnyBut('\n'))
    whitespace = Plex.Any('\f\n\r\t ')
    letter = Plex.Range('azAZ')
    digit = Plex.Range('09')
    octit = Plex.Range('07')
    underscore = Plex.Str('_')
    optsign = Plex.Opt(Plex.Any('+-'))
    name = (letter | underscore) + Plex.Rep(letter | underscore | digit)
    # XXX Hexadecimal, octal, binary?
    digits = Plex.Rep(digit)
    digits1 = Plex.Rep1(digit)
    dot = Plex.Str('.')
    integer = digits1                                   # NNNN
    intfrac = integer + Plex.Opt(dot + digits)          # NNN[.[NNNN]]
    fraconly = dot + digits1                            # .NNNN
    expmark = Plex.Any('eE')
    exponent = expmark + optsign + digits1              # (e/E)[+/-]NNN
    real = (intfrac | fraconly) + Plex.Opt(exponent)
    esc = Plex.Str('\\')
    escchar = Plex.Str(*escapes.keys())
    octal3 = octit + octit + octit

    lexicon = Plex.Lexicon([
        (whitespace,    Plex.IGNORE),
        (line_comment,  Plex.IGNORE),
        (Plex.Str('('), grammar.T_LROUND),
        (Plex.Str(')'), grammar.T_RROUND),
        (Plex.Str(','), grammar.T_COMMA),
        (Plex.Str(':'), grammar.T_COLON),
        (Plex.Str(';'), grammar.T_SEMI),
        (Plex.Str('['), grammar.T_LSQUARE),
        (Plex.Str(']'), grammar.T_RSQUARE),
        (Plex.Str('{'), grammar.T_LCURLY),
        (Plex.Str('}'), grammar.T_RCURLY),
        (Plex.Str('[|'), grammar.T_LOXFORD),
        (Plex.Str('|]'), grammar.T_ROXFORD),
        (Plex.Str('$'), grammar.T_LDOLLAR),
        (Plex.Str('?'), grammar.T_QUESTION),
        (Plex.Str('='), grammar.T_EQDEF),
        # Hack ~ to mean = everywhere but be available for reasons of
        # code style.  If we later want to adjust the system to
        # differentiate them, new tokens and grammar changes will be
        # needed.
        (Plex.Str('~'), grammar.T_EQDEF),
        (Plex.Str('<-'), grammar.T_LARR),
        # Also <~ for <-.
        (Plex.Str('<~'), grammar.T_LARR),
        (Plex.Str('->'), grammar.T_RARR),
        # Also ~> for ->.
        (Plex.Str('~>'), grammar.T_RARR),
        (Plex.Str('#'), grammar.T_HASH),
        (Plex.Str('||'), grammar.T_OR),
        (Plex.Str('&&'), grammar.T_AND),
        (Plex.Str('=='), grammar.T_EQ),
        (Plex.Str('!='), grammar.T_NEQ),
        (Plex.Str('<='), grammar.T_LE),
        (Plex.Str('>='), grammar.T_GE),
        (Plex.Str('<'),  grammar.T_LT),
        (Plex.Str('>'), grammar.T_GT),
        (Plex.Str('+'), grammar.T_ADD),
        (Plex.Str('-'), grammar.T_SUB),
        (Plex.Str('/'), grammar.T_DIV),
        (Plex.Str('*'),  grammar.T_MUL),
        (Plex.Str('**'), grammar.T_POW),
        (name + Plex.Str("<"), grammar.L_TAG),
        (name,          scan_name),
        (integer,       scan_integer),
        (real,          scan_real),
        (Plex.Str('"'), scan_string),
        (Plex.Str('@{') + name, scan_language),
        (Plex.Str('/**'), scan_comment_open),
        (Plex.AnyChar,  -1),    # Invalid -- error.
        Plex.State('STRING', [
            (Plex.Str('"'),                     scan_string_end),
            (esc + octal3,                      scan_string_octal),
            (esc + escchar,                     scan_string_escape),
            (esc + Plex.AnyChar,                scan_string_escerror),
            (Plex.Rep1(Plex.AnyBut('\\"')),     scan_string_text),
            # XXX Report EOF inside string.
        ]),
        Plex.State('LANGUAGE', [
            (Plex.AnyChar,      scan_language_char),
        ]),
        Plex.State('BLOCK_COMMENT', [
            (Plex.Str('/**'),    scan_comment_open),
            (Plex.Str('**/'),    scan_comment_close),
            (Plex.AnyChar,      Plex.IGNORE),
        ]),
    ])

    def __init__(self, file, name, languages=None):
        Plex.Scanner.__init__(self, self.lexicon, file, name)
        self.stringio = None
        self.string_start = None
        self.languages = {} if languages is None else languages
        self.current_language = None
        self.comment_level = 0

    # Override produce so we can consistently record a position with
    # each token, and use the position as character offset from the
    # start of stream as Venture wants, rather than (line, col) as
    # Plex's position() method yields.
    #
    # XXX No reason to do this other than hysterical raisins.  Fix!
    def produce(self, token, value=None, length=None):
        if token is None:       # EOF
            token = 0
        if value is None:
            value = self.text
        if length is None:
            length = len(self.text)
        end = self.cur_pos
        start = end - length
        Plex.Scanner.produce(self, token, ast.Located([start, end-1], value))
