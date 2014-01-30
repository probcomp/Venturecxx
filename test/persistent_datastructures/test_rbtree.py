from venture.lite.persistent_rbtree import RBTree

def testRBTreeEmpty():
  r = RBTree()
  assert r.isEmpty()

def testRBTreeInsertMember():
  r = RBTree()
  r1 = r.insert(1)
  assert not r1.isEmpty()
  assert r1.member(1)

def testRBTreeStressInsert():
  r = RBTree()
  N = 2000
  for i in range(N):
    r = r.insert((i * 14536777) % 107331)

  for i in range(N):
    assert r.member((i * 14536777) % 107331)

def testRBTreeIterate():
  r = RBTree()
  for i in range(1000):
    r = r.insert((i * 14536777) % 107331)

  xs = set()
  for x in r: xs.add(x)

  for i in range(1000):
    assert (i * 14536777) % 107331 in xs
