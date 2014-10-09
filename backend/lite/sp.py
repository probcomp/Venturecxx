from value import VentureValue, registerVentureType, VentureType
import copy
from exception import VentureError
import venture.value.dicts as v
from venture.lite.value import NilType

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

class SP(object):
  def __init__(self,requestPSP,outputPSP):
    from psp import PSP
    self.requestPSP = requestPSP
    self.outputPSP = outputPSP
    assert isinstance(requestPSP, PSP)
    assert isinstance(outputPSP, PSP)

  def constructSPAux(self): return SPAux()
  def constructLatentDB(self): return None
  def simulateLatents(self,spaux,lsr,shouldRestore,latentDB): pass
  def detachLatents(self,spaux,lsr,latentDB): pass
  def hasAEKernel(self): return False
  def show(self, _spaux): return "unknown spAux"
  def description(self,name):
    candidate = self.outputPSP.description(name)
    if candidate:
      return candidate
    candidate = self.requestPSP.description(name)
    if candidate:
      return candidate
    return name
  def venture_type(self):
    if hasattr(self.outputPSP, "f_type"):
      return self.outputPSP.f_type
    else:
      return self.requestPSP.f_type
  # VentureSPs are intentionally not comparable until we decide
  # otherwise

  def reifyLatent(self):
    # TODO: this method, and venture_type above, do not work for the class
    # UncollapsedHMMSP, which is the output of make_lazy_hmm. That class
    # has typed PSP's for both it's request and its output.
    if hasattr(self.outputPSP, "f_type"):
      return self.outputPSP.reifyLatent()
    else:
      return self.requestPSP.reifyLatent()

class VentureSPRecord(VentureValue):
  def __init__(self, sp, spAux=None, spFamilies=None):
    if spAux is None:
      spAux = sp.constructSPAux()
    if spFamilies is None:
      spFamilies = SPFamilies()
    self.sp = sp
    self.spAux = spAux
    self.spFamilies = spFamilies

  def show(self):
    return self.sp.show(self.spAux)

  def asStackDict(self, _trace=None):
    return v.val("sp", self.show())

registerVentureType(VentureSPRecord)

class SPType(VentureType):
  """An object representing a Venture function type.  It knows
the types expected for the arguments and the return, and thus knows
how to wrap and unwrap individual values or Args objects.  This is
used in the implementation of TypedPSP and TypedLKernel."""
  def asVentureValue(self, thing): return thing
  def asPython(self, vthing): return vthing
  def distribution(self, _base, **_kwargs):
    return None
  def __contains__(self, vthing): return isinstance(vthing, VentureSPRecord)

  def __init__(self, args_types, return_type, latent_type=NilType(),
               variadic=False, min_req_args=None):
    self.args_types = args_types
    self.return_type = return_type
    self.latent_type = latent_type
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
      if len(lst) < self.min_req_args:
        raise VentureError("Too few arguments: SP requires at least %d args, got only %d." % (self.min_req_args, len(lst)))
      if len(lst) > len(self.args_types):
        raise VentureError("Too many arguments: SP takes at most %d args, got %d." % (len(self.args_types), len(lst)))
      # v could be None when computing log density bounds for a torus
      return [self.args_types[i].asPythonNoneable(v) for (i,v) in enumerate(lst)]
    else:
      return [self.args_types[0].asPythonNoneable(v) for v in lst]

  def wrap_arg_list(self, lst):
    if not self.variadic:
      assert len(lst) >= self.min_req_args
      assert len(lst) <= len(self.args_types)
      # v could be None when computing log density bounds for a torus
      return [self.args_types[i].asVentureValue(v) for (i,v) in enumerate(lst)]
    else:
      return [self.args_types[0].asVentureValue(v) for v in lst]

  def wrap_latent(self, latent):
    return self.latent_type.asVentureValue(latent)

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

  def gradient_type(self):
    return SPType([t.gradient_type() for t in self.args_types], self.return_type.gradient_type(), self.variadic, self.min_req_args)
