from value import VentureValue, registerVentureType, VentureType
from abc import ABCMeta
import copy

class SPFamilies(object):
  def __init__(self, families=None):
    if families:
      assert type(families) is dict
      self.families = families
    else:
      self.families = {} # id => node

  def containsFamily(self,id): return id in self.families
  def getFamily(self,id): return self.families[id]
  def registerFamily(self,id,esrParent): 
    assert not id in self.families
    self.families[id] = esrParent
  def unregisterFamily(self,id): del self.families[id]

  def copy(self):
    return SPFamilies(self.families.copy())
  
class SPAux(object):
  def copy(self): return SPAux()

class VentureSP(VentureValue):
  __metaclass__ = ABCMeta

  def __init__(self,requestPSP,outputPSP):
    self.requestPSP = requestPSP
    self.outputPSP = outputPSP

  def constructSPAux(self): return SPAux()
  def constructLatentDB(self): return None
  def simulateLatents(self,spaux,lsr,shouldRestore,latentDB): pass
  def detachLatents(self,spaux,lsr,latentDB): pass
  def hasAEKernel(self): return False
  def description(self,name):
    candidate = self.outputPSP.description(name)
    if candidate:
      return candidate
    candidate = self.requestPSP.description(name)
    if candidate:
      return candidate
    return name
  # VentureSPs are intentionally not comparable until we decide
  # otherwise

registerVentureType(VentureSP)

class SPType(VentureType):
  """An object representing a Venture function type.  It knows
the types expected for the arguments and the return, and thus knows
how to wrap and unwrap individual values or Args objects.  This is
used in the implementation of TypedPSP and TypedLKernel."""
  def asVentureValue(self, thing): return thing
  def asPython(self, vthing): return vthing
  def __contains__(self, vthing): return isinstance(vthing, VentureSP)

  def __init__(self, args_types, return_type, variadic=False, min_req_args=None):
    self.args_types = args_types
    self.return_type = return_type
    self.variadic = variadic
    if variadic:
      assert len(args_types) == 1 # TODO Support non-homogeneous variadics later
    self.min_req_args = len(args_types) if min_req_args is None else min_req_args

  def wrap_return(self, value):
    return self.return_type.asVentureValue(value)
  def unwrap_return(self, value):
    # value could be None for e.g. a "delta kernel" that is expected,
    # by e.g. pgibbs, to actually be a simulation kernel; also when
    # computing log density bounds over a torus for rejection
    # sampling.
    return self.return_type.asPythonNoneable(value)
  def unwrap_args(self, args):
    if args.isOutput:
      assert not args.esrValues # TODO Later support outputs that have non-latent requesters
    answer = copy.copy(args)
    answer.operandValues = self.unwrap_arg_list(args.operandValues)
    return answer

  def unwrap_arg_list(self, lst):
    if not self.variadic:
      assert len(lst) >= self.min_req_args
      assert len(lst) <= len(self.args_types)
      # v could be None when computing log density bounds for a torus
      return [self.args_types[i].asPythonNoneable(v) for (i,v) in enumerate(lst)]
    else:
      return [self.args_types[0].asPythonNoneable(v) for v in lst]

  def _name_for_fixed_arity(self, args_types):
    args_spec = " ".join([t.name() for t in args_types])
    variadicity_mark = " ..." if self.variadic else ""
    return_spec = self.return_type.name()
    return "<SP %s%s -> %s>" % (args_spec, variadicity_mark, return_spec)

  def names(self):
    """One name for each possible arity of this procedure."""
    return [self._name_for_fixed_arity(self.args_types[0:i]) for i in range(self.min_req_args, len(self.args_types) + 1)]

  def name(self):
    """A default name for when there is only room for one name."""
    return self._name_for_fixed_arity(self.args_types)
