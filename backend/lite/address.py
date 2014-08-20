
class Address(object):
  
  def __init__(self, index, parent=None):
    self.index = index
    self.parent = parent
  
  def extend(self, index):
    return Address(index, self)
