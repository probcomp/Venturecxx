import venture.lite.types as t

from venture.mite.state import register_trace_type
from venture.mite.state import trace_action
from venture.mite.state import trace_property


class CounterState(object):
  def __init__(self):
    self.counts = {}

  def get(self, key):
    return self.counts.get(key, 0)

  def set(self, key, val):
    self.counts[key] = val

  def incr(self, key):
    self.counts[key] = self.counts.get(key, 0) + 1

  def decr(self, key):
    self.counts[key] = self.counts.get(key, 0) - 1

  def copy(self):
    ret = CounterState()
    ret.counts = self.counts.copy()
    return ret

register_trace_type("counter", CounterState, {
  "counter_get": trace_action("get", [t.Object], t.Number),
  "counter_set": trace_action("set", [t.Object, t.Number], t.Nil),
  "counter_incr": trace_action("incr", [t.Object], t.Nil),
  "counter_decr": trace_action("decr", [t.Object], t.Nil),
})
