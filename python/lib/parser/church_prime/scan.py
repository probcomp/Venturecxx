# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

# Venture lexical scanner (`Church prime', Lisp-style notation).

import StringIO

import venture.plex as Plex

from venture.parser.church_prime import grammar

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
    'assume': grammar.K_ASSUME,
    'choices': grammar.K_CHOICES,
    'continuous_inference_status': grammar.K_CONTINUOUS_INFERENCE_STATUS,
    'define': grammar.K_DEFINE,
    'force': grammar.K_FORCE,
    'get_current_exception': grammar.K_GET_CURRENT_EXCEPTION,
    'get_directive': grammar.K_GET_DIRECTIVE,
    'get_global_logscore': grammar.K_GET_GLOBAL_LOGSCORE,
    'get_state': grammar.K_GET_STATE,
    'infer': grammar.K_INFER,
    'list_directives': grammar.K_LIST_DIRECTIVES,
    'load': grammar.K_LOAD,
    'observe': grammar.K_OBSERVE,
    'predict': grammar.K_PREDICT,
    'profiler_clear': grammar.K_PROFILER_CLEAR,
    'profiler_configure': grammar.K_PROFILER_CONFIGURE,
    'profiler_list_random': grammar.K_PROFILER_LIST_RANDOM,
    'rollback': grammar.K_ROLLBACK,
    'sample': grammar.K_SAMPLE,
    'start_continuous_inference': grammar.K_START_CONTINUOUS_INFERENCE,
    'stop_continuous_inference': grammar.K_STOP_CONTINUOUS_INFERENCE,
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

class Scanner(Plex.Scanner):
    line_comment = Plex.Str(';') + Plex.Rep(Plex.AnyBut('\n'))
    whitespace = Plex.Any('\f\n\r\t ')
    letter = Plex.Range('azAZ')
    digit = Plex.Range('09')
    octit = Plex.Range('07')
    underscore = Plex.Str('_')
    optsign = Plex.Opt(Plex.Any('+-'))
    name = (letter | underscore) + Plex.Rep(letter | underscore | digit)
    # < and > are angle-brackets, which fall back to operators in grammar.y.
    operator = Plex.Str('+', '-', '*', '/', '<=', '>=', '=', '!=', '<-')
    # `foo<x>' is OK, but not a name, so we don't reject it here.
    # This fails to helpfully reject 'foo<', but that's OK -- it
    # doesn't fail to accept valid syntax.
    badname = Plex.Rep1(letter | underscore | digit | Plex.Any('-+*/=!?.'))
    # XXX Hexadecimal, octal, binary?
    digits = Plex.Rep(digit)
    digits1 = Plex.Rep1(digit)
    dot = Plex.Str('.')
    integer = optsign + digits1                         # [+/-]NNNN
    intfrac = integer + Plex.Opt(dot + digits)          # [+/-]NNN[.[NNNN]]
    fraconly = optsign + dot + digits1                  # [+/-].NNNN
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
        (Plex.Str('<'), grammar.T_LANGLE),
        (Plex.Str('>'), grammar.T_RANGLE),
        (Plex.Str('['), grammar.T_LSQUARE),
        (Plex.Str('\''), grammar.T_QUOTE),
        (Plex.Str('`'), grammar.T_BACKTICK),
        (Plex.Str(']'), grammar.T_RSQUARE),
        (Plex.Str('{'), grammar.T_LCURLY),
        (Plex.Str('}'), grammar.T_RCURLY),
        (operator,      grammar.L_OPERATOR),
        (name,          scan_name),
        (integer,       scan_integer),
        (real,          scan_real),
        (Plex.Str('"'), scan_string),
        (badname,       -1),    # Invalid -- error.
        (Plex.AnyChar,  -1),    # Invalid -- error.
        Plex.State('STRING', [
            (Plex.Str('"'),                     scan_string_end),
            (esc + octal3,                      scan_string_octal),
            (esc + escchar,                     scan_string_escape),
            (esc + Plex.AnyChar,                scan_string_escerror),
            (Plex.Rep1(Plex.AnyBut('\\"')),     scan_string_text),
            # XXX Report EOF inside string.
        ]),
    ])

    def __init__(self, file, name):
        Plex.Scanner.__init__(self, self.lexicon, file, name)
        self.stringio = None
        self.string_start = None

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
        Plex.Scanner.produce(self, token, (value, start, end - 1))
