import venture.lite.types as t

from venture.mite.state import register_trace_type
from venture.mite.state import trace_action
from venture.mite.state import trace_property


class BinomialState(object):
  def __init__(self):
    self.N = 0
    self.K = 0

  def add(self, n, k):
    self.N += n
    self.K += k

  def remove(self, n, k):
    self.N -= n
    self.K -= k

  def copy(self):
    ret = BinomialState()
    ret.N = self.N
    ret.K = self.K
    return ret

register_trace_type("binomial_state", BinomialState, {
  "binomial_N": trace_property("N", t.Int),
  "binomial_K": trace_property("K", t.Int),
  "binomial_add": trace_action("add", [t.Int, t.Int], t.Nil, deterministic=True),
  "binomial_remove": trace_action("remove", [t.Int, t.Int], t.Nil, deterministic=True),
})
