"""Random Venture values and programs.
"""

import numpy.random as npr
from venture.lite import value as v
from venture.lite.utils import normalizeList
from venture.lite import env as env
from venture.lite.psp import NullRequestPSP
from venture.lite.exception import VentureValueError

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
      elt_dist = DefaultRandomVentureValue("object") # TODO reuse class of self
    return v.VentureArray([elt_dist.generate(**kwargs) for _ in range(length)])
  def nil(self, **_kwargs):
    return v.VentureNil()
  def pair(self, size=None, first_dist=None, second_dist=None, **kwargs):
    if size is None:
      size = npr.randint(0, 30)
    left_size = npr.randint(0, size+1)
    if first_dist is None:
      first_dist = DefaultRandomVentureValue("object") # TODO reuse class of self
    if second_dist is None:
      second_dist = DefaultRandomVentureValue("object") # TODO reuse class of self
    return v.VenturePair((first_dist.generate(size=left_size, **kwargs),
                          second_dist.generate(size=size-left_size, **kwargs)))
  def simplex(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(0, 10)
    return v.VentureSimplex(normalizeList(npr.uniform(0, 1, length)))
  def dict(self, **_kwargs):
    raise Exception("Can't synthesize dicts yet")
  def mapping(self, **kwargs):
    # TODO Only synthesize a mapping of a type that is compatible with
    # the intended keys (i.e., no arrays with symbol keys).
    # For that, I need to capture the non-independence between the
    # types of different arguments to the same procedure.
    # TODO Be willing to synthesize dicts and environments
    # kind = npr.choice(["dict", "list", "array", "environment"])
    kind = npr.choice(["list", "array"])
    return getattr(self, kind)(**kwargs)
  def matrix(self, length=None, **_kwargs):
    if length is None:
      length = npr.randint(0, 10)
    return v.VentureMatrix(npr.uniform(-10, 10, (length, length))) # Square matrices
  def sp(self, **_kwargs):
    raise Exception("Can't synthesize SPs")
  def environment(self, **_kwargs):
    # TODO Implement a more interesting distribution on environments
    return env.VentureEnvironment()
  def list(self, length=None, elt_dist=None, **kwargs):
    if length is None:
      length = npr.randint(0, 10)
    if elt_dist is None:
      elt_dist = DefaultRandomVentureValue("object") # TODO reuse class of self
    return v.pythonListToVentureList(*[elt_dist.generate(**kwargs) for _ in range(length)])
  def exp(self, **_kwargs):
    # TODO Synthesizing interesting expressions is the fun part!
    return self.list(length=0)
  def object(self, depth=None, **kwargs):
    if depth is None:
      depth = npr.randint(0, 5)
    if depth == 0:
      return getattr(self, npr.choice(["number", "atom", "bool", "symbol", "nil"]))(**kwargs)
    else:
      return getattr(self, npr.choice(["array", "pair", "simplex", "matrix", "list"]))(depth=depth-1, **kwargs)

def random_args_list(sp_type):
  if not sp_type.variadic:
    dists = [t.distribution(DefaultRandomVentureValue) for t in sp_type.args_types]
  else:
    length = npr.randint(0, 10)
    dists = [sp_type.args_types[0].distribution(DefaultRandomVentureValue) for _ in range(length)]
  if any([d is None for d in dists]):
    return None
  else:
    return [d.generate() for d in dists]

def sp_random_args_list(sp):
  return random_args_list(sp.venture_type())

class BogusArgs(object):
  def __init__(self, args):
    # TODO Do I want to try to synthesize an actual real random valid Args object?
    self.operandValues = args
    self.operandNodes = [None for _ in args]
    self.isOutput = True
    self.esrValues = []
    self.env = env.VentureEnvironment()

def main():
  from venture.lite.builtin import builtInSPsList
  for (name,sp) in builtInSPsList():
    print name
    args = sp_random_args_list(sp)
    print args
    if args is not None and isinstance(sp.requestPSP, NullRequestPSP):
      try:
        answer = sp.outputPSP.simulate(BogusArgs(args))
        appropriate = True
      except ValueError:
        appropriate = False
      except VentureValueError:
        appropriate = False
      if appropriate:
        assert answer in sp.venture_type().return_type

if __name__ == "__main__": main()
