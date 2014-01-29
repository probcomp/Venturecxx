from venture.lite.persistent_rbtree import RBTree

class TestRBTreeExtended():
  _multiprocess_can_split_ = True

  def setup(self): self.r = RBTree()

  def testEmpty(self):
    assert self.r.isEmpty()

  def testInsertMember(self):
    r1 = self.r.insert(1)
    assert not r1.isEmpty()
    assert r1.member(1)

  def testStressInsert(self):
    r = self.r
    for i in range(1000):
      r = r.insert((i * 14536777) % 107331)

    for i in range(1000):
      assert r.member((i * 14536777) % 107331)

