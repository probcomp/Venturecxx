from nose.tools import assert_equals # Pylint misses metaprogrammed names pylint:disable=no-name-in-module

def assertTorus(scaffold):
  for _,regenCount in scaffold.regenCounts.iteritems(): 
    assert regenCount == 0

def assertTrace(trace,scaffold):
  for node in scaffold.regenCounts:
    assert trace.valueAt(node) is not None

def assertSameScaffolds(scaffoldA,scaffoldB):
  assert_equals(len(scaffoldA.regenCounts),len(scaffoldB.regenCounts))
  assert_equals(len(scaffoldA.absorbing),len(scaffoldB.absorbing))
  assert_equals(len(scaffoldA.aaa),len(scaffoldB.aaa))
  assert_equals(len(scaffoldA.border),len(scaffoldB.border))
  for node in scaffoldA.regenCounts:
    assert_equals(scaffoldA.getRegenCount(node),scaffoldB.getRegenCount(node))

