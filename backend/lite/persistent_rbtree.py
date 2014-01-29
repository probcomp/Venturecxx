# Based on CXX code found at:
# https://raw.github.com/BartoszMilewski/Okasaki/master/RBTree/RBTree.h

# Red == True
# Black == False
 
# The two invariants:

# 1. No RED node has a RED child.
# 2. Every path from root to empty node contains the same
#    number of black nodes.

class RBNode(object):
  def __init__(self,color,left,val,right):
    self.color = color
    self.left = left
    self.val = val
    self.right = right

class RBTree(object):
  def __init__(self,root=None,color=None,left=None,val=None,right=None): 
    if root is None:
      if color is None: self.root = None
      else:
        assert left.isEmpty() or left.root.val < val
        assert right.isEmpty() or right.root.val > val
        self.root = RBNode(color,left.root,val,right.root)
    else: self.root = root

  def isEmpty(self): return self.root is None
  def left(self):
    assert not self.isEmpty()
    return RBTree(self.root.left)
  def right(self):
    assert not self.isEmpty()
    return RBTree(self.root.right)
  def member(self,x):
    if self.isEmpty(): return False
    y = self.root.val
    if x < y: return self.left().member(x)
    if y < x: return self.right().member(x)
    else: return True
        
  def insert(self,x):
    t = self.ins(x)
    return RBTree(None,"black",t.left(),t.root.val,t.right())

#   1. No red node has a red child.
  def assert1(self):
    if not self.isEmpty():
      left = self.left()
      right = self.right()
      if self.root.color == "red":
        assert left.isEmpty() or left.root.color == "black"
        assert right.isEmpty() or right.root.color == "black"
      left.assert1()
      right.assert1()

#   2. Every path from root to empty node contains the same
#      number of black nodes.

  def countB(self):
    if self.isEmpty(): return 0
    left = self.left().countB()
    right = self.right().countB()
    assert left == right
    return left + 1 if self.root.color == "black" else left

  def ins(self,x):
    self.assert1()
    if self.isEmpty(): return RBTree(None,"red",RBTree(),x,RBTree())
    y = self.root.val
    c = self.root.color
    if c == "black":
      if x < y: return self.balance(self.left().ins(x),y,self.right())
      elif y < x: return self.balance(self.left(),y,self.right().ins(x))
      else: return self
    else:
      if x < y: return RBTree(None,c,self.left().ins(x),y,self.right())
      elif y < x: return RBTree(None,c,self.left(),y,self.right().ins(x))
      else: return self

  def balance(self,left,x,right):
    if left.doubledLeft(): 
      return RBTree(None,
                    "red",
                    left.left().paint("black"),
                    left.root.val,
                    RBTree(None,"black",left.right(),x,right))
    elif left.doubledRight():
      return RBTree(None,
                    "red",
                    RBTree(None,"black",left.left(),left.root.val,left.right().left()),
                    left.right().root.val,
                    RBTree(None,"black",left.right().right(),x,right))
    elif right.doubledLeft():
      return RBTree(None,
                    "red",
                    RBTree(None,"black",left,x,right.left().left()),
                    right.left().root.val,
                    RBTree(None,"black",right.left().right(),right.root.val,right.right()))
    elif right.doubledRight():
      return RBTree(None,
                    "red",
                    RBTree(None,"black",left,x,right.left()),
                    right.root.val,
                    right.right().paint("black"))
    else:
      return RBTree(None,"black",left,x,right)

  def doubledLeft(self):
    return not self.isEmpty() and self.root.color == "red" \
           and not self.left().isEmpty() and self.left().root.color == "red"

  def doubledRight(self):
    return not self.isEmpty() and self.root.color == "red" \
           and not self.right().isEmpty() and self.right().root.color == "red"

  def paint(self,color):
    assert not self.isEmpty()
    return RBTree(None,color,self.left(),self.root.val,self.right())


# void forEach(RBTree<T> const & t, F f) {
#     if (!t.isEmpty()) {
#         forEach(t.left(), f);
#         f(t.root());
#         forEach(t.right(), f);
#     }
# }

# template<class T, class Beg, class End>
# RBTree<T> insert(RBTree<T> t, Beg it, End end)
# {
#     if (it == end)
#         return t;
#     T item = *it;
#     auto t1 = insert(t, ++it, end);
#     return t1.insert(item);
# }

