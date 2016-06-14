import random
from venture.engine import engine

class Engine(object):

  def __init__(self, backend, seed):
    self.engine = engine.Engine(backend, seed)

  def __getattr__(self, attr):
    print 'Engine method:', attr
    return getattr(self.engine, attr)

  def __setattr__(self, attr, val):
    if attr != "engine":
      return setattr(self.engine, attr, val)
    else:
      return object.__setattr__(self, attr, val)

class Engine(engine.Engine):
  def init_inference_trace(self):
    import venture.mite.trace as trace
    return trace.Trace(self._py_rng.randint(1, 2**31 - 1))
