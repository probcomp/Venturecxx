import sys
import importlib

from nose.tools import make_decorator

from venture.test.config import gen_on_inf_prim

def gen_for_each(items):
  def wrap(f):
    @make_decorator(f)
    def wrapped():
      for item in items:
        yield f, item
    return wrapped
  return wrap

sys.path.append('examples/mite/')

@gen_on_inf_prim("none")
@gen_for_each(["figure_rejection", "figure_rmh", "figure_drift", "figure_beta_bern", "figure_bayes"])
def testFigure(script_name):
  importlib.import_module(script_name).compute_results(1)
