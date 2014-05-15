import json
import warnings

class Placeholder(object):
    """An object that can be instantiated before knowing what type it should be."""
    pass

type_to_str = {}
str_to_type = {}

def register(cls):
    """Register a Python class (e.g. a custom SP) with the serializer."""

    if not isinstance(cls, type):
        raise TypeError("serialize.register() argument must be a class")

    msg = "Class does not define {0}, using fallback implementation"
    if not hasattr(cls, 'serialize') and not hasattr(cls, 'deserialize'):
        warnings.warn(msg.format("serialize() or deserialize()"), stacklevel=2)
    elif not hasattr(cls, 'serialize'):
        warnings.warn(msg.format("serialize()"), stacklevel=2)
    elif not hasattr(cls, 'deserialize'):
        warnings.warn(msg.format("deserialize()"), stacklevel=2)

    type_to_str[cls] = cls.__name__
    str_to_type[cls.__name__] = cls

    # return the class so that this can be used as a decorator
    return cls

class Serializer(object):
    """Serializer and deserializer for Trace objects."""

    def serialize_trace(self, root, extra):
        """Serialize a Trace object."""

        ## set up data structures for handling reference cycles
        self.obj_data = []
        self.obj_to_id = {}

        ## add built-in SP specially
        for name, node in root.globalEnv.outerEnv.frame.iteritems():
            self.obj_to_id[node.madeSP] = 'builtin:' + name

        ## serialize recursively
        serialized_root = self.serialize(root)
        serialized_extra = self.serialize(extra)
        return {
            'root': serialized_root,
            'objects': self.obj_data,
            'extra': serialized_extra,
            'version': '0.1'
        }

    def serialize(self, obj):
        if isinstance(obj, (bool, int, long, float, str, type(None))):
            return obj
        elif isinstance(obj, list):
            return [self.serialize(o) for o in obj]
        elif isinstance(obj, tuple):
            value = tuple(self.serialize(o) for o in obj)
            return {'_type': 'tuple', '_value': value}
        elif isinstance(obj, set):
            value = [self.serialize(o) for o in obj]
            return {'_type': 'set', '_value': value}
        elif isinstance(obj, dict):
            value = [(self.serialize(k), self.serialize(v)) for (k, v) in obj.iteritems()]
            return {'_type': 'dict', '_value': value}
        else:
            assert type(obj) in type_to_str, "Can't serialize {0}".format(repr(obj))

            ## some objects should be stored by reference, in case of shared objects and cycles
            should_make_ref = getattr(obj, 'cyclic', False)
            if should_make_ref:
                ## check if seen already
                if obj in self.obj_to_id:
                    return {'_type': 'ref', '_value': self.obj_to_id[obj]}
                ## generate a new id and append a placeholder to the obj_data array
                i = len(self.obj_data)
                self.obj_to_id[obj] = i
                self.obj_data.append(None)

            ## attempt to use the object's serialize method if available
            ## fallback: just get the __dict__
            if hasattr(obj, 'serialize'):
                serialized = obj.serialize(self)
            else:
                serialized = dict((k, self.serialize(v)) for (k, v) in obj.__dict__.iteritems())
            data = {'_type': type_to_str[type(obj)], '_value': serialized}

            if should_make_ref:
                ## store the actual data in the obj_data array and return the index instead
                self.obj_data[i] = data
                return {'_type': 'ref', '_value': i}
            else:
                return data

    def deserialize_trace(self, data):
        """Deserialize a serialized trace, producing a Trace object."""

        assert data['version'] == '0.1', "Incompatible version or unrecognized object"

        ## create placeholder object references so that we can rebuild cycles
        ## attach to each placeholder object the data dict that goes with it
        self.id_to_obj = {}
        for i, obj_dict in enumerate(data['objects']):
            obj = Placeholder()
            obj._data = obj_dict
            self.id_to_obj[i] = obj

        ## add built-in SP specially
        from trace import Trace
        for name, node in Trace().globalEnv.outerEnv.frame.iteritems():
            self.id_to_obj['builtin:' + name] = node.madeSP

        root = self.deserialize(data['root'])
        extra = self.deserialize(data['extra'])
        return root, extra

    def deserialize(self, data):
        if isinstance(data, (bool, int, long, float, str, type(None))):
            return data
        elif isinstance(data, unicode):
            ## json returns unicode strings; convert them back to str
            ## TODO: are actual unicode strings used anywhere?
            return data.encode('utf-8')
        elif isinstance(data, list):
            return [self.deserialize(o) for o in data]
        else:
            assert isinstance(data, dict), "Unrecognized object {0}".format(repr(obj))
            assert '_type' in data, "_type missing from {0}".format(repr(obj))
        if data['_type'] == 'tuple':
            return tuple(self.deserialize(o) for o in data['_value'])
        elif data['_type'] == 'set':
            return set(self.deserialize(o) for o in data['_value'])
        elif data['_type'] == 'dict':
            return dict((self.deserialize(k), self.deserialize(v)) for (k, v) in data['_value'])
        else:
            ## if it's a ref, look up the real object
            if data['_type'] == 'ref':
                obj = self.id_to_obj[data['_value']]
                try:
                    ## get the data dict we attached to the placeholder object earlier
                    data = obj._data
                    del obj._data
                except AttributeError:
                    ## already deserialized, just return the object
                    return obj
            else:
                obj = Placeholder()

            assert data['_type'] in str_to_type, "Can't deserialize {0}".format(repr(obj))
            cls = str_to_type[data['_type']]
            obj.__class__ = cls

            ## attempt to use the object's deserialize method if available
            ## fallback: just set the __dict__
            if hasattr(cls, 'deserialize'):
                obj.deserialize(self, data['_value'])
            else:
                obj.__dict__ = dict((k, self.deserialize(v)) for (k, v) in data['_value'].iteritems())

            return obj

def save_trace(trace, extra, fname):
    obj = Serializer().serialize_trace(trace, extra)
    with open(fname, 'w') as fp:
        json.dump(obj, fp)

def load_trace(fname):
    with open(fname) as fp:
        obj = json.load(fp)
    trace, extra = Serializer().deserialize_trace(obj)
    return trace, extra
