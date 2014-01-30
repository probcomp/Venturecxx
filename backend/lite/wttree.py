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

# Style note: all node keys and subtress are always listed in function
# arguments in-order.

class EmptyNode(object): #pylint: disable=W0232
  def size(self):
    return 0

class Node(object):
  def __init__(self, left, key, value, right):
    self.left = left
    self.key = key
    self.value = value
    self.right = right
    self.ct = left.size() + right.size() + 1

  def size(self):
    return self.ct

# TODO Manually inline this?
def node_weight(node):
  return node.size() + 1

def single_left(x, akey, avalue, r):
  return Node(Node(x, akey, avalue, r.left), r.key, r.value, r.right)

def single_right(l, bkey, bvalue, z):
  return Node(l.left, l.key, l.value, Node(l.right, bkey, bvalue, z))

def double_left(x, akey, avalue, r):
  return Node(Node(x, akey, avalue, r.left.left),
              r.left.key, r.left.value,
              Node(r.left.right, r.key, r.value, r.right))

def double_right(l, ckey, cvalue, z):
  return Node(Node(l.left, l.key, l.value, l.right.left),
              l.right.key, l.right.value,
              Node(l.right.right, ckey, cvalue, z))

# For the provenance of these constants, see Yoichi Hirai and Kazuhiko
# Yamamoto, `Balancing Weight-Balanced Trees', Journal of Functional
# Programming 21(3), 2011.
_DELTA = 3
_GAMMA = 2

def t_join(l, key, value, r):
  l_w = node_weight(l)
  r_w = node_weight(r)
  if r_w > _DELTA * l_w:
    # Right is too big
    if node_weight(r.left) < _GAMMA * node_weight(r.right):
      return single_left(l, key, value, r)
    else:
      return double_left(l, key, value, r)
  elif l_w > _DELTA * r_w:
    # Left is too big
    if node_weight(l.right) < _GAMMA * node_weight(l.left):
      return single_right(l, key, value, r)
    else:
      return double_right(l, key, value, r)
  else:
    return Node(l, key, value, r)

# Testing TODO:
# - Correctness, per Daniel's rbtree tests
# - Balance, either as asymptotics with the timings framework or
#   through an explicit check.
