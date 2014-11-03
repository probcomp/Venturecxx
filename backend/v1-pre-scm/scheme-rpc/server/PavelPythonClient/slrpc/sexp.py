# From the pylisp project
# https://github.com/pavpanchekha/pylisp/blob/master/pylisp/sexp.py

r"""
The `sexp` module parses the special subset of sexps
that pylisp supports. Where by subset I mean sorta-related
set. There is only one function you should be using: parse.

>>> parse('''(+ "Hello, " 'World (* '! ({x: {{x + 2}}} 3)))''')
[['+', ["'", 'Hello, '], ["'", 'World'], ['*', ["'", '!'], [['fn', ['x'], ['pyeval', ["'", 'x + 2']]], 3]]]]

Note that the code returns a list of sexps. This might
eventually change to a generator-based approach, but for now
this provides a simple way to deal with code examples.

All other functions in this module follow the "eat" protocol,
wherein they are fed in a string, and return a (value, rest)
pair, where `rest` is the rest of the string not yet
processed. It's perhaps best to think of this as a
continuation of sorts. All of the eating functions are
prefixed with "eat_". If the input passed to such a function
is invalid, it by convention returns "" and eats nothing
(that is, it returns `("", s)` if passed an invalid `s`.
"""

from collections import namedtuple

DEBUG = False
traceindent = 0
def trace(f):
    def wrapped(*args, **kwargs):
        global traceindent
        if DEBUG:
            print(" "*traceindent, f.__name__, "->")
            traceindent += 2
        res = f(*args, **kwargs)
        if DEBUG:
            traceindent -= 2
            print(" "*traceindent, "<-", res)
        return res
    return wrapped

Cons = namedtuple("Cons", ["car", "cdr"])

Symbol = namedtuple("Symbol", ["name"])

class UnreadableReadableStream:
    def __init__(self, stream):
        self.stream = stream
        self.unread_chars = ""

    def read(self, l):
        unread = self.unread_chars[:l]
        self.unread_chars = self.unread_chars[len(unread):]
        if l == len(unread):
            return unread
        else:
            new = self.stream.read(l - len(unread))
            if DEBUG:
                import sys
                sys.stdout.write(new)
            return unread + new

    def unread(self, chars):
        # TODO: Replace with faster, not O(n) algorithm
        self.unread_chars = chars + self.unread_chars

    def peek(self, l):
        a = self.read(l)
        self.unread(a)
        return a

prefixes = []

def prefix(name):
    prefixes.append(name)

@trace
def eat_name(stream):
    """
    Eat a name, following the eat protocol.

    >>> eat_name("xyz stuff")
    ('xyz', ' stuff')
    >>> eat_name("xyz(")
    ('xyz', '(')
    >>> eat_name("xyz;comment")
    ('xyz', ';comment')
    >>> eat_name("0")
    ('', '0')
    """
    
    num = ""
    char = stream.read(1)
    
    while char and char not in "(){}; \t\n\v\f":
        num += char
        char = stream.read(1)
        
    stream.unread(char)

    if num:
        return Symbol(num)
    else:
        return ""

@trace
def eat_number(stream):
    """
    Eat a float or integer.

    >>> eat_number("0")
    (0, '')
    >>> eat_number(".5")
    (0.5, '')
    >>> eat_number("1.5 ;comment")
    (1.5, ' ;comment')
    >>> eat_number("five")
    ('', 'five')
    """
    
    num = ""
    char = stream.read(1)

    read_count = ""
    
    if char not in "0123456789.e-+":
        stream.unread(char)
        return ""

    while char and char in "0123456789.e-+":
        num += char
        read_count += char
        char = stream.read(1)

    stream.unread(char)

    try:
        if "." in num or "e" in num:
            return float(num)
        else:
            return int(num)
    except ValueError:
        stream.unread(read_count)
        return None

@trace
def eat_str(stream):
    """
    Eat a double-quoted string.

    >>> eat_str('''"asdf"''')
    (["'", 'asdf'], '')
    >>> eat_str('''"" ;adsf''')
    (["'", ''], ' ;adsf')
    >>> eat_str("asdf")
    ('', 'asdf')
    """
    
    s = ""
    char = stream.read(1)

    if char != '"':
        stream.unread(char)
        return ""

    char = stream.read(1)

    while char and char != '"':
        if char == "\\":
            char = stream.read(1)
            if char == "\n":
                pass
            else:
                s += eval("\"\\{0}\"".format(char))
            char = stream.read(1)
        else:
            s += char
            char = stream.read(1)

    return s

@trace
def eat_ws(stream):
    """
    Eat a bunch of whitespace.
    """

    char = stream.read(1)

    while char and char.isspace():
        char = stream.read(1)

    stream.unread(char)
    
    return None

@trace
def eat_sexp(stream):
    """
    Eat a full s-expression.

    >>> eat_sexp("(+ 1 2)")
    (['+', 1, 2], '')
    >>> eat_sexp("((1 2) (2 3) (4 (1 2) (3 4)))")
    ([[1, 2], [2, 3], [4, [1, 2], [3, 4]]], '')
    >>> eat_sexp("+ 1 2")
    ('', '+ 1 2')
    """

    char = stream.read(1)

    if char != "(":
        stream.unread(char)
        return ""

    retval = []
    while char and char != ")":
        char = stream.read(1)
        if char in " \t\n\v)":
            pass
        elif char != ")":
            stream.unread(char)
            sexp = eat_value(stream)
            retval.append(sexp)
            eat_ws(stream)

    return fix_improper(retval)

def fix_improper(lst):
    """
    Return ``lst``, or an instance of ``Cons`` if the list is in fact
    a pair literal; if ``lst`` is an improper list, raises an error,
    as these are not supported.
    """

    if len(lst) == 3 and lst[1] == ".":
        return Cons(lst[0], lst[2])
    elif len(lst) >= 2 and lst[-2] == ".":
        raise NotImplementedError
    elif "." in lst:
        raise SyntaxError
    else:
        return lst

@trace
def eat_comment(s):
    """
    Eat a comment (comments are semicolons and then to the
    end of the line).

    >>> eat_comment("; adsf\\n; asdf")
    ('', '\\n; asdf')
    >>> eat_comment("a")
    ('', 'a')
    """
    
    char = stream.read(1)

    if char != ";":
        stream.unread(char)
        return ""
    
    while char and char != "\n":
        char = stream.read(1)

    return ""

prefix("'")
prefix("`")
prefix(",")
prefix(",@")
prefix("#:")

@trace
def eat_value(stream):
    """
    Eat a value in general. Will choose from other "eat_x"
    functions.
    """

    eat_ws(stream)
    
    char = stream.read(1)
    stream.unread(char)
    
    if not char:
        raise EOFError
    elif char == ";":
        eat_comment(stream)
        return eat_value(stream)
    elif char == "(":
        return eat_sexp(stream)
    elif char in "0123456789.+-e":
        out = eat_number(stream)
        if out is not None: return out
    
    maxprefix = len(max(prefixes, key=len))
    prefix_maybe = stream.peek(maxprefix)

    poss_pref = [pref for pref in prefixes if prefix_maybe.startswith(pref)]
    if poss_pref:
        pref = sorted(poss_pref, key=len)[-1]
        stream.read(len(poss_pref))
        sexp = eat_value(stream)
        return [pref, sexp]
    elif char == '"':
        return eat_str(stream)
    else:
        sexp = eat_name(stream)
        if sexp in map(Symbol, ["#t", "#f", "#0"]):
            sexp = {"#t": True, "#f": False, "#0": None}[sexp.name]
        return sexp

def parse(stream):
    stream = UnreadableReadableStream(stream)
    while True:
        try:
            sexp = eat_value(stream)
        except EOFError:
            stop = True
        else:
            stop = False

        if stop:
            raise StopIteration
        else:
            yield sexp

if __name__ == "__main__":
    import doctest
    doctest.testmod()
