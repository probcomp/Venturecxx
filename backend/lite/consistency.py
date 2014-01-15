import pdb

def assertTorus(scaffold):
  for node,regenCount in scaffold.regenCounts.iteritems(): 
    if regenCount != 0: pdb.set_trace()

def assertTrace(trace,scaffold):
  for node in scaffold.regenCounts:
    assert trace.valueAt(node) is not None
