from collections import OrderedDict
from contextlib import contextmanager

from typing import Iterator # Pylint doesn't understand type comments pylint: disable=unused-import
from typing import Optional # pylint: disable=unused-import

import venture.lite.value as vv

class Trace(vv.VentureValue):
  def __init__(self):
    # type: () -> None
    self.value = None # type: Optional[vv.VentureValue]
    self.subtraces = OrderedDict() # type: OrderedDict[vv.VentureValue, Trace]
    self._reified = False

  @contextmanager
  def subtrace(self, key):
    # type: (vv.VentureValue) -> Iterator[Trace]
    if key not in self.subtraces:
      self.subtraces[key] = Trace()
    try:
      yield self.subtraces[key]
    finally:
      if key in self.subtraces and \
         not self.subtraces[key]._reified and \
         not self.subtraces[key].has() and \
         not self.subtraces[key].subtraces:
        del self.subtraces[key]

  @contextmanager
  def subexpr_subtrace(self, index):
    # type: (int) -> Iterator[Trace]
    with self.subtrace(vv.VentureInteger(index)) as t:
      yield t

  @contextmanager
  def definition_subtrace(self):
    # type: () -> Iterator[Trace]
    with self.subtrace(vv.VentureString("def")) as t:
      yield t

  @contextmanager
  def literal_subtrace(self):
    # type: () -> Iterator[Trace]
    with self.subtrace(vv.VentureString("lit")) as t:
      yield t

  @contextmanager
  def predicate_subtrace(self):
    # type: () -> Iterator[Trace]
    with self.subtrace(vv.VentureString("p")) as t:
      yield t

  @contextmanager
  def consequent_subtrace(self):
    # type: () -> Iterator[Trace]
    with self.subtrace(vv.VentureString("t")) as t:
      yield t

  @contextmanager
  def alternate_subtrace(self):
    # type: () -> Iterator[Trace]
    with self.subtrace(vv.VentureString("f")) as t:
      yield t

  def reify(self):
    # type: () -> None
    self._reified = True

  def has(self):
    # type: () -> bool
    return self.value is not None

  def get(self):
    # type: () -> vv.VentureValue
    assert self.value is not None
    return self.value

  def set(self, value):
    # type: (vv.VentureValue) -> None
    self.value = value

  def clear(self):
    # type: () -> None
    self.value = None

  def update(self, trace):
    # type: (Trace) -> None
    if trace.has():
      self.set(trace.get())
    for k, d in trace.subtraces.iteritems():
      with self.subtrace(k) as s:
        s.update(d)

  def sites(self):
    # type: () -> List[vv.VentureValue]
    # Actually a list of Venture lists of VentureValues, but I haven't coded
    # Venture Lists to be an appropriate generic type.
    ans = [] # type: List[vv.VentureValue]
    if self.has():
      ans.append(vv.VentureNil())
    for k, d in self.subtraces.iteritems():
      for site in d.sites():
        ans.append(vv.VenturePair((k, site)))
    return ans

  def lookup(self, key):
    # type: (vv.VentureValue) -> Trace
    with self.subtrace(key) as ans:
      ans.reify()
      return ans

  def get_at(self, key):
    # type: (List[vv.VentureValue]) -> vv.VentureValue
    if len(key) == 0:
      return self.get()
    else:
      with self.subtrace(key[0]) as s:
        return s.get_at(key[1:])

  def __repr__(self):
    if self.subtraces:
      return "Trace(%r, %r)" % (self.value, list(self.subtraces.iteritems()))
    else:
      return "Trace(%r)" % (self.value,)

@contextmanager
def subtrace_at(trace, keys):
  if len(keys) == 0:
    yield trace
  else:
    with trace.subtrace(keys[0]) as t2:
      with subtrace_at(t2, keys[1:]) as s:
        yield s
