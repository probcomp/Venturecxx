class EmptyList(object):
  def __iter__(self):
    return
    yield
  
  def __len__(self):
    return 0
  
  def __repr__(self):
    return str(list(self))
  
  def prepend(self, first):
    return List(first, self)

  def map(self, f):
    return self
  
emptyList = EmptyList()

class List(object):
  
  def __init__(self, first, rest=emptyList):
    assert(first is not None)
    assert(rest is not None)
    self.first = first
    self.rest = rest
  
  # FIXME: quadratic runtime :(
  # needs python 3's "yield from"
  def __iter__(self):
    yield self.first
    for i in self.rest:
      yield i
  
  def __len__(self):
    return 1 + len(self.rest)
  
  def __repr__(self):
    return str(list(self))
  
  def prepend(self, first):
    return List(first, self)

  def map(self, f):
    return self.rest.map(f).prepend(f(self.first))

class Address(List):
  """Maintains a call stack."""
  def __init__(self, index, stack=emptyList):
    super(Address, self).__init__(index, stack)
  
  def request(self, index):
    """Make a new stack frame."""
    return self.prepend(index)
  
  def extend(self, index):
    """Extend the current stack frame."""
    return Address(self.first.prepend(index), self.rest)
  
  def asList(self):
    """Converts to nested lists."""
    return map(list, list(self))
