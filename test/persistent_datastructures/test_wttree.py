from venture.lite.wttree import Map

def testMapInsertContainsDelete():
  r = Map()
  assert len(r) == 0
  assert not r # Things with len == 0 register as False in Python

  r1 = r.insert(1,2)
  assert r1 # Things with len != 0 register as True
  assert len(r1) == 1
  assert 1 in r1
  assert len(r) == 0
  assert 1 not in r

  r2 = r1.delete(1)
  assert 1 in r1
  assert 1 not in r2
  assert len(r2) == 0

def _hash(i):
  return (i * 14536777) % 107331

def testMapStressInsertDelete():
  r = Map()
  N = 2000
  for i in range(N):
    r = r.insert(_hash(i), True)

  for i in range(N):
    assert _hash(i) in r

  r2 = r
  for i in range(N/2,N):
    r2 = r2.delete(_hash(i))

  for i in range(N/2):
    assert _hash(i) in r
    assert _hash(i) in r2

  for i in range(N/2,N):
    assert _hash(i) in r
    assert _hash(i) not in r2

def testMapIterate():
  r = Map()
  for i in range(1000):
    r = r.insert(_hash(i), i)

  xs = dict()
  for (k,v) in r.iteritems(): xs[k] = v

  for i in range(1000):
    assert xs[_hash(i)] == i
