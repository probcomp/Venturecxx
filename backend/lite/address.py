
class Address(object):
  
  def __init__(self, index, parent=None):
    self.index = index
    self.parent = parent
  
  def extend(self, index):
    return Address(index, self)
  
  def __iter__(self):
    if self.parent:
      for i in self.parent:
        yield i
    yield self.index
  
  def __repr__(self):
    return str(list(self))
