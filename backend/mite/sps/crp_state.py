from collections import OrderedDict

import venture.lite.types as t

from venture.mite.state import (register_trace_type,
                                trace_property,
                                trace_action)


class CRPState(object):
  def __init__(self):
    self.table_counts = OrderedDict()
    self.next_table = 1
    self.num_customers = 0

  def seat(self, table, incr):
    # Seat incr customers at the given table.
    # Incr will be +1 or -1.
    self.num_customers += incr
    if table in self.table_counts:
      self.table_counts[table] += incr
    else:
      self.table_counts[table] = incr
    if self.table_counts[table] == 0:
      del self.table_counts[table]
    if table == self.next_table:
      self.next_table += 1

  def copy(self):
    ret = CRPState()
    ret.table_counts.update(self.table_counts)
    ret.next_table = self.next_table
    ret.num_customers = self.num_customers
    return ret

register_trace_type("crp_state", CRPState, {
  "crp_table_counts": trace_property("table_counts", t.Dict(t.Atom, t.Int)),
  "crp_next_table": trace_property("next_table", t.Atom),
  "crp_seat": trace_action("seat", [t.Atom, t.Int], t.Nil),
})
