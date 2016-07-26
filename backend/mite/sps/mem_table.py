import venture.lite.types as t

from venture.mite.state import (register_trace_type,
                                trace_property,
                                trace_action)


class MemTable(object):
  def __init__(self):
    self.value_map = {}         # key -> value
    self.num_requests = {}      # key -> count

  def has_value(self, key):
    return key in self.value_map

  def lookup(self, key):
    return self.value_map[key]

  def assoc(self, key, value):
    self.value_map[key] = value

  def incr(self, key):
    pass

  def copy(self):
    # TODO
    return self

register_trace_type("mem_table", MemTable, {
  "mem_has_value": trace_action("has_value", [t.Object], t.Bool),
  "mem_lookup": trace_action("lookup", [t.Object], t.Object),
  "mem_assoc": trace_action("assoc", [t.Object, t.Object], t.Nil),
  "mem_incr": trace_action("incr", [t.Object], t.Nil),
})
