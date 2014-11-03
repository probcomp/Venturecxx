import socket
import sexp
import common
import warnings
import remotes
import sys
class AssertionWarning(Warning): pass

PY3K = sys.version_info[0] == 3

ROOT_CONTINUATION = [[sexp.Symbol("%roots"),
                      sexp.Cons("the-root-car", "the-root-cdr")]]

class TheReturnContinuation(remotes.RemoteProcedure):
    def __init__(self, client):
        remotes.RemoteProcedure.__init__(self, client, "the-return-continuation", "#[continuation 0]", (1, 1))

    def __call__(self, x):
        return x

    def marshal(self):
        out = remotes.RemoteProcedure.marshal(self)
        out[1][0] = sexp.Symbol("soid")
        out[1][2] = [sexp.Symbol("cont"), False]
        return out

class RPCClient:    
    def __init__(self, addr):
        self.addr = addr
        self.connect()

        self.RETURN = TheReturnContinuation(self)
        self.object_table = {
            "the-return-continuation": self.RETURN,
            }

    def connect(self):
        self.seqno = 0;
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect(self.addr)

        if PY3K:
            self.sendf = soc.makefile(mode="w", encoding="utf-8")
            self.recvf = soc.makefile(mode="r", encoding="utf-8")
        else:
            self.sendf = soc.makefile(mode="w")
            self.recvf = soc.makefile(mode="r")

    def call(self, cmd, *args):
        seqno = self.seqno
        self.seqno += 1
        
        data = [cmd, list(args), ROOT_CONTINUATION, self.RETURN]
        message = [sexp.Symbol("cinvoke"), seqno, ["`", data]]

        common.write_sexp(message, self.sendf)
        self.sendf.flush()

        response = next(sexp.parse(self.recvf))
        return self.parse_response(response, seqno)

    def parse_response(self, response, seqno):
        cmd = response[0]

        if not isinstance(cmd, sexp.Symbol):
            raise SystemError("Command in response not a symbol")
            cmd = sexp.Symbol(cmd)

        if response[1] != seqno:
            warnings.warn("Sequence numbers don't match", AssertionWarning)

        if cmd.name == "cinvoke" and len(response) == 3 and \
                len(response[2]) == 2 and response[2][0] == "`" and \
                len(response[2][1]) == 4 and \
                isinstance(self.unmarshal(response[2][1][0]), remotes.RemoteObject) and \
                self.unmarshal(response[2][1][0]) == self.RETURN and \
                response[2][1][2] and not response[2][1][3] and \
                len(response[2][1][1]) == 1:
            return self.unmarshal(response[2][1][1][0])
        elif cmd.name == "cinvoke":
            raise SystemError("Can't parse cinvoke {0}".format(response))
        elif cmd.name == "drop":
            if len(response) == 2 and response[1] in ("the-root-car",
                                                      "the-root-cdr",
                                                      "the-return-continuation"):
                pass
            else:
                raise SystemError("Asked to drop {0}; help!".format(response))
        elif cmd.name == "proto-error":
            raise SystemError(response[1][1])
        else:
            raise SystemError("Unknown message; help!", response)

    def h_cinvoke(self, seqno, cmd):
        assert cmd[0] == "`", "Expected quasiquoted list for cinvoke"
        fn, args, roots, retcont = cmd

        fn = self.unmarshal(fn)
        args = self.unmarshal(args)

        return fn(*args)

    def unmarshal(self, val):
        if isinstance(val, list) and len(val) == 2 and val[0] == "," and \
                isinstance(val[1], list):
            fn, args = val[1][0], val[1][1:]
            try:
                return getattr(self, "f_" + fn.name)(*args)
            except (AttributeError, TypeError) as e:
                raise RuntimeError("Unknown RPC function {0}".format(fn))
        elif isinstance(val, list):
            return [self.unmarshal(elt) for elt in val]
        else:
            return val

    def f_oid(self, id, desc):
        if id in self.object_table:
            return self.object_table[id]
        print(id, self.object_table)

        obj = self.make_remote(id, desc)
        self.object_table[id] = obj
        return obj

    def f_soid(self, id, desc):
        if id in self.object_table:
            return self.object_table[id]


        obj = self.make_remote(id, desc, strong=True)
        self.object_table[id] = obj
        return obj

    def make_remote(self, id, desc, strong=False):
        if not isinstance(desc, list) or len(desc) == 0:
            raise KeyError("Unknown remote object {0}".format(id), desc)

        if desc[0] == sexp.Symbol("robj"):
            return remotes.RemoteObject(self, id, desc[1], strong=strong)
        elif desc[0] == sexp.Symbol("proc"):
            return remotes.RemoteProcedure(self, id, desc[1], desc[2], strong=strong)
        elif desc[0] == sexp.Symbol("cont"):
            return remotes.RemoteProcedure(self, id, "#[continuation]", (0, 1), strong=strong)
        else:
            raise RuntimeError("Unknown remote object type {0}".format(desc[0]), desc)

    def drop(self, id):
        # TODO TODO TODO
        pass
