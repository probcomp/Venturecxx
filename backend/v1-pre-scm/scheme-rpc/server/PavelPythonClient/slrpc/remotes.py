import common
import sexp

class RemoteObject:
    def __init__(self, client, id, desc, strong=False):
        self.client = client
        self.id = id
        self.desc = desc
        self.strong = strong

    def __eq__(self, other):
        return self.id == other.id and self.client == other.client

    def __del__(self):
        if self.strong:
            self.client.drop(self.id)

        del self.client.object_table[self.id]

    def __repr__(self):
        return "<remote object {0} on {1}>".format(self.desc, self.client)

    def marshal(self):
        return [",", [sexp.Symbol("oid"), self.id, False]]

class RemoteProcedure(RemoteObject):
    def __init__(self, client, id, name, args, strong=False):
        RemoteObject.__init__(self, client, id, name, strong=strong)
        self.minargs = args[0]
        self.maxargs = args[1]

    def __repr__(self):
        return "<remote function {0} on {1}>".format(self.desc, self.client)

    def __call__(self, *args):
        assert self.minargs <= len(args) <= self.maxargs, "{0} must have between {1} and {2} arguments".format(self, self.minargs, self.maxargs)
        return self.client.call(self.marshal(), *args)
