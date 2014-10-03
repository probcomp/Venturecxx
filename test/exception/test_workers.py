from sys import exc_info
from testconfig import config

from venture.test.config import get_ripl
from venture.exception import VentureException

def test_no_traces():
  '''If no errors occurred, there should be no worker traces'''
  ripl = get_ripl()
  ripl.infer('(resample 2)')
  ripl.assume('x', 10)
  traces = ripl.get_worker_traces()
  assert traces is None

def get_traceback_type():
  '''Can't find how to import type traceback directly, so here's a hack'''
  try: raise ValueError
  except ValueError:
    _, _, tb = exc_info()
  return type(tb)

def get_exception_type():
  if config['get_ripl'] == 'lite':
    return VentureException
  else:
    return RuntimeError

def test_traces():
  '''If errors occurred, there should be worker traces'''
  traceback = get_traceback_type()
  ripl = get_ripl()
  ripl.infer('(resample 2)')
  ripl.assume('x', 10)
  try: ripl.assume('x', 10)
  except get_exception_type():
    pass
  traces = ripl.get_worker_traces()
  assert len(traces) == 2
  assert all([isinstance(trace, traceback) for trace in traces])
