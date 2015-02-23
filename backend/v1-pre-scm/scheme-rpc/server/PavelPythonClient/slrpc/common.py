from collections import namedtuple 
import sexp

Address = namedtuple("Address", ["ip", "port"])

def write_sexp(value, file):
    #print(value)
    def output(val):
        #print(val, end="", sep="")
        file.write(val)
    
    if isinstance(value, bool):
        output("#t" if value else "#f")
    elif isinstance(value, int) or isinstance(value, long) or isinstance(value, float):
        output(str(value))
    elif isinstance(value, str):
        output('"{0}"'.format(repr(value)[1:-1]))
    elif isinstance(value, sexp.Symbol):
        output(value.name)
    elif isinstance(value, list):
        if len(value) > 0 and isinstance(value[0], str) and \
                value[0] in sexp.prefixes:
            assert len(value) == 2, "Invalid prefixed string thing"
            output(value[0])
            write_sexp(value[1], file)
        else:
            output("(")
            for elt in value:
                write_sexp(elt, file)
                output(" ")
            output(")")
    elif isinstance(value, sexp.Cons):
        output("(")
        write_sexp(value.car, file)
        output(" . ")
        write_sexp(value.cdr, file)
        output(")")
    elif hasattr(value, "marshal"):
        write_sexp(value.marshal(), file)
    else:
        raise ValueError("Don't know how to serialize {0} to sexp".format(value))
