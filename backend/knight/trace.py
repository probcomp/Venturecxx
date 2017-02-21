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
      if not self.subtraces[key]._reified and \
         not self.subtraces[key].has() and \
         not self.subtraces[key].subtraces:
        del self.subtraces[key]

  @contextmanager
  def subexpr_subtrace(self, index):
    # type: (int) -> Iterator[Trace]
    with self.subtrace(vv.VentureInteger(index)) as t:
      yield t

  @contextmanager
  def application_subtrace(self):
    # type: () -> Iterator[Trace]
    with self.subtrace(vv.VentureString("app")) as t:
      yield t

  @contextmanager
  def definition_subtrace(self):
    # type: () -> Iterator[Trace]
    with self.subtrace(vv.VentureString("def")) as t:
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

  def __repr__(self):
    if self.subtraces:
      return "Trace(%r, %r)" % (self.value, list(self.subtraces.iteritems()))
    else:
      return "Trace(%r)" % (self.value,)
