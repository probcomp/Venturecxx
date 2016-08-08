import venture.lite.types as t

from venture.mite.state import register_trace_type
from venture.mite.state import trace_action


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
    self.num_requests[key] = 0

  def incr(self, key):
    self.num_requests[key] += 1

  def decr(self, key):
    self.num_requests[key] -= 1

  def count(self, key):
    return self.num_requests[key]

  def dissoc(self, key):
    assert self.num_requests[key] == 0
    del self.num_requests[key]
    del self.value_map[key]

  def copy(self):
    # TODO
    return self

register_trace_type("mem_table", MemTable, {
  "mem_has_value": trace_action("has_value", [t.Object], t.Bool),
  "mem_lookup": trace_action("lookup", [t.Object], t.Object),
  "mem_assoc": trace_action("assoc", [t.Object, t.Object], t.Nil),
  "mem_incr": trace_action("incr", [t.Object], t.Nil),
  "mem_decr": trace_action("decr", [t.Object], t.Nil),
  "mem_count": trace_action("count", [t.Object], t.Int),
  "mem_dissoc": trace_action("dissoc", [t.Object], t.Nil),
})
