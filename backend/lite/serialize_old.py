import json
import warnings

import numpy as np

class Placeholder(object):
    """An object that can be instantiated before knowing what type it should be."""
    pass

type_to_str = {}
str_to_type = {}

def register(cls):
    """Register a Python class (e.g. a custom SP) with the serializer."""

    if not isinstance(cls, type):
        raise TypeError("serialize.register() argument must be a class")

    # msg = "Class does not define {0}, using fallback implementation"
    # if not hasattr(cls, 'serialize') and not hasattr(cls, 'deserialize'):
    #     warnings.warn(msg.format("serialize() or deserialize()"), stacklevel=2)
    # elif not hasattr(cls, 'serialize'):
    #     warnings.warn(msg.format("serialize()"), stacklevel=2)
    # elif not hasattr(cls, 'deserialize'):
    #     warnings.warn(msg.format("deserialize()"), stacklevel=2)

    type_to_str[cls] = cls.__name__
    str_to_type[cls.__name__] = cls

    # return the class so that this can be used as a decorator
    return cls

class Serializer(object):
    """Serializer and deserializer for Trace objects."""

    def serialize_trace(self, root):
        """Serialize a Trace object."""

        ## set up data structures for handling reference cycles
        self.queue = []
        self.obj_data = []
        self.obj_to_id = {}

        ## add built-in SP specially
        for name, node in root.globalEnv.outerEnv.frame.iteritems():
            self.obj_to_id[node.madeSP] = 'builtin:' + name

        ## serialize recursively
        serialized_root = self.serialize(root)
        for obj in self.queue:
            self.obj_data.append(self.serialize(obj, should_make_ref=False))
        return {
            'root': serialized_root,
            'objects': self.obj_data,
        }

    def serialize(self, obj, should_make_ref=True):
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
        elif isinstance(obj, np.ndarray):
            # TODO: do something more compatible with Puma
            value = obj.dumps().encode('base64')
            return {'_type': 'array', '_value': value}
        else:
            assert type(obj) in type_to_str, "Can't serialize {0}".format(repr(obj))

            ## some objects should be stored by reference, in case of shared objects and cycles
            if should_make_ref and getattr(obj, 'cyclic', False):
                ## check if seen already
                if obj in self.obj_to_id:
                    return {'_type': 'ref', '_value': self.obj_to_id[obj]}
                ## generate a new id and append the object to the queue
                ## return a reference to the index of the object in the queue
                i = len(self.queue)
                self.obj_to_id[obj] = i
                self.queue.append(obj)
                return {'_type': 'ref', '_value': i}

            ## attempt to use the object's serialize method if available
            if hasattr(obj, 'serialize'):
                serialized = obj.serialize(self)
            else:
                serialized = self.serialize_default(obj)
            data = {'_type': type_to_str[type(obj)], '_value': serialized}
            return data

    def serialize_default(self, obj):
        ## fallback serialization method: just get the __dict__
        return dict((k, self.serialize(v)) for (k, v) in obj.__dict__.iteritems())

    def deserialize_trace(self, data):
        """Deserialize a serialized trace, producing a Trace object."""

        ## create placeholder object references so that we can rebuild cycles
        ## attach to each placeholder object the data dict that goes with it
        self.id_to_obj = {}
        self.queue = []
        for i, obj_dict in enumerate(data['objects']):
            obj = Placeholder()
            self.id_to_obj[i] = obj
            self.queue.append((obj_dict, obj))

        ## add built-in SP specially
        from trace import Trace
        for name, node in Trace().globalEnv.outerEnv.frame.iteritems():
            self.id_to_obj['builtin:' + name] = node.madeSP

        root = self.deserialize(data['root'])
        for (obj_dict, obj) in self.queue:
            self.deserialize(obj_dict, obj)
        return root

    def deserialize(self, data, obj=None):
        if isinstance(data, (bool, int, long, float, str, type(None))):
            return data
        elif isinstance(data, unicode):
            ## json returns unicode strings; convert them back to str
            ## TODO: are actual unicode strings used anywhere?
            return data.encode('utf-8')
        elif isinstance(data, list):
            return [self.deserialize(o) for o in data]
        else:
            assert isinstance(data, dict), "Unrecognized object {0}".format(repr(data))
            assert '_type' in data, "_type missing from {0}".format(repr(data))
        if data['_type'] == 'tuple':
            return tuple(self.deserialize(o) for o in data['_value'])
        elif data['_type'] == 'set':
            return set(self.deserialize(o) for o in data['_value'])
        elif data['_type'] == 'dict':
            return dict((self.deserialize(k), self.deserialize(v)) for (k, v) in data['_value'])
        elif data['_type'] == 'array':
            return np.loads(data['_value'].decode('base64'))
        else:
            ## if it's a ref, look up the real object
            if data['_type'] == 'ref':
                obj = self.id_to_obj[data['_value']]
                return obj

            assert data['_type'] in str_to_type, "Can't deserialize {0}".format(repr(data))
            cls = str_to_type[data['_type']]

            if obj is None:
                obj = Placeholder()
            obj.__class__ = cls

            ## attempt to use the object's deserialize method if available
            if hasattr(obj, 'deserialize'):
                obj.deserialize(self, data['_value']) # pylint: disable=maybe-no-member
            else:
                self.deserialize_default(obj, data['_value'])

            return obj

    def deserialize_default(self, obj, value):
        ## fallback deserialization method: just set the __dict__
        obj.__dict__ = dict((k, self.deserialize(v)) for (k, v) in value.iteritems())

def dump_trace_old(trace):
    return Serializer().serialize_trace(trace)

def restore_trace_old(obj):
    return Serializer().deserialize_trace(obj)
