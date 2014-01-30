from venture.lite.wttree import Map

def testMapInsertContainsDelete():
  r = Map()
  r1 = r.insert(1,2)
  assert r1.contains(1)
  assert not r.contains(1)
  r2 = r1.delete(1)
  assert r1.contains(1)
  assert not r2.contains(1)

def testMapStressInsertDelete():
  r = Map()
  N = 2000
  for i in range(N):
    r = r.insert((i * 14536777) % 107331, True)

  for i in range(N):
    assert r.contains((i * 14536777) % 107331)

  r2 = r
  for i in range(N/2,N):
    r2 = r2.delete((i * 14536777) % 107331)

  for i in range(N/2):
    assert r.contains((i * 14536777) % 107331)
    assert r2.contains((i * 14536777) % 107331)

  for i in range(N/2,N):
    assert r.contains((i * 14536777) % 107331)
    assert not r2.contains((i * 14536777) % 107331)

# def testMapIterate():
#   r = Map()
#   for i in range(1000):
#     r = r.insert((i * 14536777) % 107331)

#   xs = set()
#   for x in r: xs.add(x)

#   for i in range(1000):
#     assert (i * 14536777) % 107331 in xs
