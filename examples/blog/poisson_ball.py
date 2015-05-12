import venture.ripl.utils as u

def __venture_start__(ripl):
  ripl.bind_callback('data_dump', data_dump)

def data_dump(_, ds, file_name):
  ds = u.strip_types(ds)[0].asPandas()
  from IPython.core.debugger import Pdb; Pdb('Linux').set_trace()

def chisquare_vs_blog(_, ds):
  ds = u.strip_types(ds)[0].asPandas()
  counts = ds.n_balls.value_counts()
  max = counts.index.max()
  from IPython.core.debugger import Pdb; Pdb('Linux').set_trace()
  print counts[range(0, int(max + 1))].fillna(0)
