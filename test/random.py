"""Random Venture values and programs.
"""

import numpy.random as npr
from venture.lite import value as v
from venture.lite.utils import normalizeList

class DefaultRandomVentureValue(object):
  def __init__(self, method, **kwargs):
    self.method = method
    self.kwargs = kwargs
  def generate(self, **kwargs):
    return getattr(self, self.method)(**(dict(self.kwargs.items() + kwargs.items())))
  def number(self, **_kwargs):
    return v.VentureNumber(npr.uniform(-10, 10))
  def atom(self, **_kwargs):
    return v.VentureAtom(npr.randint(-10, 11)) # Open at the top
  def bool(self, **_kwargs):
    return v.VentureBool(npr.choice([False, True]))
  def symbol(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(0, 10)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return v.VentureSymbol(''.join(npr.choice(list(alphabet), length)))
  def array(self, length=None, elt_dist=None, **kwargs):
    if length is None:
      length = npr.randint(0, 10)
    if elt_dist is None:
      elt_dist = DefaultRandomVentureValue("any") # TODO reuse class of self
    return v.VentureArray([elt_dist.generate(**kwargs) for _ in range(length)])
  def nil(self, **_kwargs):
    return v.VentureNil()
  def pair(self, size=None, elt_dist=None, **kwargs):
    if size is None:
      size = npr.randint(0, 30)
    left_size = npr.randint(0, size+1)
    if elt_dist is None:
      elt_dist = DefaultRandomVentureValue("any") # TODO reuse class of self
    return v.VenturePair(elt_dist.generate(size=left_size, **kwargs),
                         elt_dist.generate(size=size-left_size, **kwargs))
  def simplex(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(0, 10)
    return v.VentureSimplex(normalizeList(npr.uniform(-10, 10, length)))
  def dict(self, **_kwargs):
    raise Exception("Can't synthesize dicts yet")
  def matrix(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(0, 10)
    return v.VentureMatrix(npr.uniform(-10, 10, (length, length))) # Square matrices
  def sp(self, **_kwargs):
    raise Exception("Can't synthesize SPs")
  def environment(self, **_kwargs):
    raise Exception("Can't synthesize environments yet")
  def list(self, length=None, elt_dist=None, **kwargs):
    if length is None:
      length = npr.randint(0, 10)
    if elt_dist is None:
      elt_dist = DefaultRandomVentureValue("any") # TODO reuse class of self
    return v.pythonListToVentureList(*[elt_dist.generate(**kwargs) for _ in range(length)])
  def object(self, size=None, **kwargs):
    if size is None:
      size = npr.randint(0, 30)
    if size == 0:
      return getattr(self, npr.choice(["number", "atom", "bool", "symbol", "nil"]))(**kwargs)
    else:
      return getattr(self, npr.choice(["array", "pair", "simplex", "matrix", "list"]))(size=size-1, **kwargs)

def random_args_list(sp_type):
  return [t.distribution(DefaultRandomVentureValue).generate() for t in sp_type.args_types]

def sp_random_args_list(sp):
  return random_args_list(sp.outputPSP.f_type)

if __name__ == "__main__":
  from venture.lite.builtin import builtInSPsList
  for (name,sp) in builtInSPsList():
    print name
    print sp_random_args_list(sp)

