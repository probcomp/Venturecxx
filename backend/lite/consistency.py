import pdb

def assertTorus(scaffold):
  for node,regenCount in scaffold.regenCounts.iteritems(): 
    if regenCount != 0: pdb.set_trace()
