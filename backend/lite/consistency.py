def assertTorus(scaffold):
  for _,regenCount in scaffold.regenCounts.iteritems(): 
    assert regenCount == 0

def assertTrace(trace,scaffold):
  for node in scaffold.regenCounts:
    assert trace.valueAt(node) is not None

def assertSameScaffolds(scaffoldA,scaffoldB):
  assert len(scaffoldA.regenCounts) == len(scaffoldB.regenCounts)
  assert len(scaffoldA.absorbing) == len(scaffoldB.absorbing)
  assert len(scaffoldA.aaa) == len(scaffoldB.aaa)
  assert len(scaffoldA.border) == len(scaffoldB.border)
  for node in scaffoldA.regenCounts:
    assert scaffoldA.getRegenCount(node) == scaffoldB.getRegenCount(node)

