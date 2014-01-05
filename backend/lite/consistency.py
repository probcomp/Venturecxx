import pdb

def assertTorus(scaffold):
  for node in scaffold.drg: 
    if scaffold.drg[node] != 0: pdb.set_trace()
