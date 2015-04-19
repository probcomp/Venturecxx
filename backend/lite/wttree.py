# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

'''Weight-balanced trees.

This program is based on

  Stephen Adams, Implementing Sets Efficiently in a Functional
     Language, CSTR 92-10, Department of Electronics and Computer
     Science, University of Southampton, 1992.

but only implements the operations that are useful for Venture Lite.
The actual implementation is cribbed close to verbatim from wt-trees
in MIT Scheme, which were written by Stephen Adams and modified by
Chris Hanson and Taylor Campbell.'''

# TODO I imagine much memory can be saved by representing the
# node structure with just a tuple and None, manely
# data Tree k v = Maybe (k,v,Node k v,Node k v,Int)
# instead of the below classes
# data Tree k v = Either EmptyNode (Node k v)

# Style note: all node keys and subtress are always listed in function
# arguments in-order.

class EmptyNode(object): #pylint: disable=W0232
  def size(self): return 0
  def isEmpty(self): return True

class Node(object):
  def __init__(self, left, key, value, right):
    self.left = left
    self.key = key
    self.value = value
    self.right = right
    self.ct = left.size() + right.size() + 1

  def size(self): return self.ct
  def isEmpty(self): return False

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

def node_popmin(node):
  if node.isEmpty():
    raise Exception("Trying to pop the minimum off an empty node")
  elif node.left.isEmpty():
    return (node.key, node.value, node.right)
  else:
    # TODO Is this constant creation and desctruction of tuples
    # actually any more efficient than just finding the minimum in one
    # pass and removing it in another?
    (mink, minv, newl) = node_popmin(node.left)
    return (mink, minv, t_join(newl, node.key, node.value, node.right))

def node_lookup(node, key):
  if node.isEmpty():
    return None
  elif key < node.key:
    return node_lookup(node.left, key)
  elif node.key < key:
    return node_lookup(node.right, key)
  else:
    return node.value

def node_insert(node, key, value):
  if node.isEmpty():
    return Node(EmptyNode(), key, value, EmptyNode())
  elif key < node.key:
    return t_join(node_insert(node.left, key, value),
                  node.key, node.value, node.right)
  elif node.key < key:
    return t_join(node.left, node.key, node.value,
                  node_insert(node.right, key, value))
  else:
    return Node(node.left, key, value, node.right)

def node_adjust(node, key, f):
  if node.isEmpty():
    # TODO Optimize the not-found case by not reconstructing the tree
    # on the way up?
    return node
  elif key < node.key:
    return Node(node_adjust(node.left, key, f),
                node.key, node.value, node.right)
  elif node.key < key:
    return Node(node.left, node.key, node.value,
                node_adjust(node.right, key, f))
  else:
    return Node(node.left, key, f(node.value), node.right)

def node_delete(node, key):
  if node.isEmpty():
    return node
  elif key < node.key:
    return t_join(node_delete(node.left, key),
                  node.key, node.value, node.right)
  elif node.key < key:
    return t_join(node.left, node.key, node.value,
                  node_delete(node.right, key))
  else:
    # Deleting the key at this node
    if node.right.isEmpty():
      return node.left
    elif node.left.isEmpty():
      return node.right
    else:
      [min_r_k, min_r_v, new_r] = node_popmin(node.right)
      return t_join(node.left, min_r_k, min_r_v, new_r)

def node_traverse_in_order(node):
  if not node.isEmpty():
    for pair in node_traverse_in_order(node.left): yield pair
    yield (node.key, node.value)
    for pair in node_traverse_in_order(node.right): yield pair

def node_traverse_keys_in_order(node):
  if not node.isEmpty():
    for key in node_traverse_keys_in_order(node.left): yield key
    yield node.key
    for key in node_traverse_keys_in_order(node.right): yield key

class PMap(object):
  """Persistent map backed by a weight-balanced tree.

  The lookup method returns None if the key is not found.  Do not
  insert None as a value or you will get confused."""
  def __init__(self, root=None):
    self.root = root if root is not None else EmptyNode()
  def lookup(self, key):
    return node_lookup(self.root, key)
  def __contains__(self, key):
    return node_lookup(self.root, key) is not None
  def insert(self, key, value):
    return PMap(node_insert(self.root, key, value))
  def adjust(self, key, f):
    """adjust :: (PMap k v) -> k -> (v -> v) -> PMap k v

    Returns a new PMap obtained from this one by applying the given
    function to the value at the given key.  Returns the original PMap
    unchanged if the key is not present.  The name is chosen by
    analogy to Data.PMap.adjust from the Haskell standard library."""
    return PMap(node_adjust(self.root, key, f))
  def delete(self, key):
    return PMap(node_delete(self.root, key))

  def __len__(self): return self.root.size()
  def __iter__(self):
    return node_traverse_keys_in_order(self.root)
  def iteritems(self):
    return node_traverse_in_order(self.root)

class PSet(object):
  """Persistent set backed by a weight-balanced tree.

  At present, happens to be implemented just like a PMap, but with the
  values always being True.  In principle could be impemented more
  efficiently by specializing the nodes not to store values at all."""
  def __init__(self, root=None):
    self.root = root if root is not None else EmptyNode()
  def __contains__(self, key):
    return node_lookup(self.root, key) is not None
  def insert(self, key):
    return PSet(node_insert(self.root, key, True))
  def delete(self, key):
    return PSet(node_delete(self.root, key))

  def __len__(self): return self.root.size()
  def __iter__(self):
    return node_traverse_keys_in_order(self.root)

# TODO test balance, either as asymptotics with the timings framework
# or through an explicit check that a tree built by some mechanism is
# balanced.  Issue https://app.asana.com/0/9277419963067/9924589720809
