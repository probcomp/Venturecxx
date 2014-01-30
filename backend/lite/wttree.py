'''Weight-balanced trees.

This program is based on

  Stephen Adams, Implementing Sets Efficiently in a Functional
     Language, CSTR 92-10, Department of Electronics and Computer
     Science, University of Southampton, 1992.

but only implements the operations that are useful for Venture Lite.
The actual implementation is cribbed close to verbatim from wt-trees
in MIT Scheme, which were written by Stephen Adams and modified by
Chris Hansen and Taylor Campbell.'''

# TODO I imagine much memory can be saved by representing the
# node structure with just a tuple and None, manely
# data Tree k v = Maybe (k,v,Node k v,Node k v,Int)
# instead of the below classes
# data Tree k v = Either EmptyNode (Node k v)

class EmptyNode: #pylint: disable=W0232
  def size(self):
    return 0

class Node:
  def __init__(self, key, value, left, right):
    self.key = key
    self.value = value
    self.left = left
    self.right = right
    self.ct = left.size() + right.size() + 1

  def size(self):
    return self.ct

# TODO Manually inline this?
def node_weight(node):
  return node.size() + 1
