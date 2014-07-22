from itertools import chain
import numpy.random as npr

class Node(object):
  """Binary tree to speed up categorical sampling."""
  def __init__(self, vals):
    self.leaf = len(vals) == 1
    
    if self.leaf:
      self.total = vals[0]
    else:
      self.mid = len(vals) // 2
      self.left = Node(vals[:self.mid])
      self.right = Node(vals[self.mid:])
      self.total = self.left.total + self.right.total
  
  def __getitem__(self, index):
    if self.leaf:
      return self.total
    elif index < self.mid:
      return self.left[index]
    else:
      return self.right[index - self.mid]
  
  def adjust(self, index, f):
    if self.leaf:
      self.total = f(self.total)
    elif index < self.mid:
      self.left.adjust(index, f)
    else:
      self.right.adjust(index - self.mid, f)
  
  def increment(self, index):
    self.adjust(index, lambda x: x+1)
  
  def decrement(self, index):
    self.adjust(index, lambda x: x-1)
  
  def __setitem__(self, index, value):
    self.adjust(index, lambda _: value)
  
  def __iter__(self):
    if self.leaf:
      yield self.total
    else:
      for leaf in chain(self.left, self.right):
        yield leaf
  
  def leaves(self):
    return list(self)
  
  def __len__(self):
    if self.leaf:
      return 1
    else:
      return len(self.left) + len(self.right)

def sample(*nodes):
  n = nodes[0]
  
  if n.leaf: return 0
  
  total = sum(node.total for node in nodes)
  left = sum(node.left.total for node in nodes)
  
  if npr.randint(total) < left:
    return sample(*[node.left for node in nodes])
  else:
    return n.mid + sample(*[node.right for node in nodes])
