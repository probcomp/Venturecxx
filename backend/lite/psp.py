# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureBuiltinSPMethodError
from venture.lite.lkernel import DefaultVariationalLKernel
from venture.lite.lkernel import DeterministicMakerAAALKernel
from venture.lite.lkernel import LKernel
from venture.lite.request import Request
from venture.lite.typing import List
from venture.lite.typing import TYPE_CHECKING
from venture.lite.utils import override
import venture.lite.value as vv

if TYPE_CHECKING:
  from venture.lite.node import Node

class PSP(object):
  """A Primitive Stochastic Procedure.

  PSPs are the basic units of computation in Venture.  A PSP
  represents a (potentially) stochastic process that computes a value
  conditioned on some arguments (A PSP may instead compute a set of
  requests for further evaluation by Venture -- this is how compound
  Venture procedures are implemented -- but this is an advanced
  topic).

  The PSP interface is for people wishing to extend Venture with
  bindings to additional external computations (including traditional
  foreign functions, as well as things like a custom inference method
  for a particular model type).  Users of Venture who do not wish to
  extend it need not learn the PSP interface.

  The main part of the PSP interface is about providing information
  about the stochastic process the PSP represents -- simulating from
  it, computing log densities, etc.  Generally only the ability to
  simulate is required to define a valid PSP, but implementing the
  other methods may improve efficiency and/or permit the application
  of additional inference methods to scaffolds containing the PSP in
  question.

  The PSP interface also currently contains several methods used for
  the selection of lkernels, pending the invention of a better
  mechanism.  If you don't know what lkernels are, don't worry about
  it -- the defaults will do.

  The general pattern of PSP methods is that they accept an IArgs
  instance (and possibly some additional arguments) and compute
  something about the stochastic process in the context given by that
  IArgs instance.  The
  main thing the IArgs object contains is the list of arguments this
  stochastic process is applied to, but it also has a bunch of
  additional contextual information that can be useful for special
  PSPs.  See below for the definition of IArgs.

  The data members of the IArgs object will generally be represented as
  Venture values (instances of the venture.lite.value.VentureValue
  class).  The data returned from psp methods should generally also be
  instances of the VentureValue class, except methods that yield
  information for direct consumption by the engine itself (such as the
  isRandom method).  See doc/type-system.md for the design.

  Most of the time, the requisite marshalling between VentureValues
  and corresponding Python representations is mechanical boilerplate,
  which can be taken care of for you by the TypedPSP class, which see.
  """

  def simulate(self, _args):
    # type: (IArgs) -> vv.VentureValue
    """Simulate this process with the given parameters and return the result."""
    raise VentureBuiltinSPMethodError("Simulate not implemented!")

  def gradientOfSimulate(self, _args, _value, _direction):
    # type: (IArgs, vv.VentureValue, vv.VentureValue) -> List[vv.VentureValue]
    """Return the gradient of this PSP's simulation function.  This method
    is needed only for Hamiltonian Monte Carlo.

    Specifically, the gradient of the simulation function must be with
    respect to the given direction on the output space, at the point
    given by the args struct (the input space is taken to be the full
    list of parents).  In other words, the Jacobian-vector product

      direction^T J_simulate(args).

    For PSPs with one scalar output, the direction will be a number,
    and the correct answer is the gradient of simulate multiplied by
    that number.

    The gradient should be returned as a list of the partial
    derivatives with respect to each parent node represented in the
    args.

    We circumvent problems with trying to compute derivatives of
    stochastic functions by mixing over the randomness consumed.  What
    this practically means is that the gradient to be computed is the
    gradient of the deterministic function of the arguments that is
    this process, if its randomness is fixed at some particular stream
    of bits.  The gradient will, in general, depend on what those bits
    are.  Pending a better interface for communicating it, the value
    argument of this method is the value that simulating this PSP
    outputs when using the fixed randomness with respect to which the
    gradient is to be computed.  We hope that, for sufficiently simple
    PSPs, this proxy is sufficient.

    The exact circumstances when this method is needed for HMC are
    this PSP appearing as the operator of a non-principal,
    non-absorbing scaffold node (that is, in the non-principal part of
    the DRG, or in the brush).
    """
    raise VentureBuiltinSPMethodError("Cannot compute simulation gradient of %s",
      type(self))

  def isRandom(self):
    # type: () -> bool
    """Return whether this PSP is stochastic or not.  This is important
    because only nodes whose operators are random PSPs can be
    principal.
    """
    raise VentureBuiltinSPMethodError("Do not know whether %s is random",
      type(self))

  def canAbsorb(self, _trace, _appNode, _parentNode):
    """Return whether this PSP, which is the operator of the given
    application node, can absorb a change to the value of the given
    parent node.

    If this returns True, then logDensity must return a finite value
    for any proposed new value of the given parent node.  canAbsorb
    calls are assumed to be cumulative: if a PSP claims to be able to
    absorb changes to two of its parents individually, that amounts to
    claiming to absorb changes to both of them simultaneously.
    """
    raise VentureBuiltinSPMethodError("Do not know whether %s can absorb",
      type(self))

  def logDensity(self, _value, _args):
    # type: (vv.VentureValue, IArgs) -> float
    """Return the log-density of simulating the given value from the given args.

    If the output space is discrete, return the log-probability.

    Note: Venture does *not* ensure that the given value actually was
    simulated from the given args.  The ability to measure the density
    of other values (or of the same value at other args) is invaluable
    for many inference methods.

    Implementing this method is not strictly necessary for a valid
    PSP, but is very helpful for many purposes if the density
    information is available.  See also canAbsorb.
    """
    raise VentureBuiltinSPMethodError("Cannot compute log density of %s",
      type(self))

  def gradientOfLogDensity(self, _value, _args):
    """Return the gradient of this PSP's logDensity function.  This method
    is needed only for gradient-based methods (currently Hamiltonian
    Monte Carlo and Meanfield).

    The gradient should be returned as a 2-tuple of the partial
    derivative with respect to the value and a list of the partial
    derivatives with respect to the arguments."""
    raise VentureBuiltinSPMethodError("Cannot compute gradient of log density "
      "of %s", type(self))

  def logDensityBound(self, _value, _args):
    """Return an upper bound on the possible log density of this PSP
    holding the given values fixed.  This method is needed only for
    rejection sampling.

    Specifically, the value and any or all of the operands present in
    the IArgs instance may be None.  Return an upper bound on the value
    the logDensity function could take for any values substituted for
    the None arguments, but holding fixed the given non-None
    arguments.  See NormalOutputPSP for an example implementation.

    This method is used only when this PSP is the operator of an
    absorbing node under rejection sampling.  Tighter upper bounds
    lead to more efficient rejection sampling.

    TODO maybe allow the logDensityBound to return None to indicate no
    bound, and in this case do not try to absorb at this node when
    doing rejection sampling?  Or should that be a separate method
    called logDensityBounded?
    """
    raise VentureBuiltinSPMethodError("Cannot compute log density bound of %s",
      type(self))

  def incorporate(self,value,args):
    """Register that an application of this PSP produced the given value
    at the given args.  This is relevant only if the SP needs to
    maintain statistics about results of its applications (e.g., for
    collapsed models, or for external inference schemes that need to
    maintain statistics).
    """
    pass

  def unincorporate(self,value,args):
    """Unregister one instance of an application of this PSP producing the
    given value at the given args.  This is the inverse of
    incorporate.
    """
    pass

  def logDensityOfData(self, _aux):
    """Return the log-density of simulating a dataset with the given
    collected statistics.

    This is relevant only for PSPs that collect statistics about their
    uses via incorporate and unincorporate that are sufficient to bulk
    absorb at all applications of the PSP, without traversing them.

    Specifically return the sum of the log-density at each application
    of this PSP; which is also the joint log-density of producing any
    one permutation of the observed output sequence.  For some
    distributions (e.g., Poisson), this may not be computable from the
    traditional sufficient statisitc; in such a case, the sufficient
    statistic should be augmented with sufficient information to
    compute this.  For rationales for this specification, see
    doc/on-log-density-of-counts.md.
    """
    raise VentureBuiltinSPMethodError("Cannot compute log density of data of "
      "%s", type(self))

  def canEnumerate(self):
    """Return whether this PSP can enumerate the space of its possible
    return values.  Enumeration is used only for principal nodes in
    enumerative Gibbs.
    """
    return False

  # Returns a Python list of VentureValue objects
  def enumerateValues(self, _args):
    """Return a list of all the values this PSP can return given the
    arguments.  Enumeration is used only for principal nodes in
    enumerative Gibbs.

    For enumerative Gibbs to work, logDensity must return a finite
    number for the probability of every value returned from this
    method, given the same arguments.
    """
    raise VentureBuiltinSPMethodError("Cannot enumerate %s.", type(self))

  def description(self, _name):
    """Return a string describing this PSP.  The string may include the
    name argument, which is the symbol that the enclosing SP is bound to.
    """
    return None

  def description_rst_format(self, _name):
    return None

  def childrenCanAAA(self):
    return False

  def getAAALKernel(self):
    raise VentureBuiltinSPMethodError("%s has no AAA LKernel", type(self))

  def hasVariationalLKernel(self):
    return False

  def getVariationalLKernel(self,args):
    return DefaultVariationalLKernel(self, args)

  def hasSimulationKernel(self):
    return False

  def hasDeltaKernel(self):
    return False

  def marginalLogDensityOfData(self, _aux, _args):
    """Return the marginal of the made PSP's logDensityOfData function,
    integrating over the output distribution of the maker for the
    given args. This method is relevant only for random makers of PSPs
    that collect sufficient statistics via incorporate and
    unincorporate.

    """
    # a return value of NotImplemented means "defer to the made PSP's
    # logDensityOfData" (suitable for deterministic makers).
    # TODO: should this method replace logDensityOfData?
    return NotImplemented

  def gradientOfLogDensityOfData(self, _aux, _args):
    """Return the gradient of the made PSP's logDensityOfData function.
    This method is needed only for gradient-based methods and is
    relevant only for makers of PSPs that collect sufficient
    statistics via incorporate and unincorporate.

    The gradient should be returned as a list of the partial
    derivatives with respect to the arguments.

    """
    raise VentureBuiltinSPMethodError("Cannot compute gradient of log density of data of %s", type(self))

  def madeSpLogDensityOfDataBound(self, _aux):
    """Upper bound the logDensityOfData the made SP may report for the
    given aux, up to arbitrary changes to the args wherewith the maker
    is simulated.

    TODO Communicate the maker's fixed parameters here to enable more
    precise bounds.
    """
    raise VentureBuiltinSPMethodError("Cannot rejection auto-bound AAA procedure "
      "with unbounded log density of data.")

class IArgs(object):
  """The evaluation context against which a (P)SP is executed.

  This class serves as a container for documentation about the
  evaluation context interface Lite (P)SPs expect.

  """
  def __init__(self):
    # type: () -> None
    self.operandNodes = [] # type: List[Node]
    """The identities of the arguments passed to the PSP.

    These are used primarily by parametrically polymorphic PSPs, like
    the RequestPSP in the implementation of lambda and the maker
    corresponding to mem.
    """
    self.node = None
    """The identity of the current application itself.

    This is used mainly as a unique key to prevent auto-caching of
    requests that are supposed to be generative.
    """
    self.env = VentureEnvironment() # type: VentureEnvironment[Node]
    """The lexical environment of the application.

    This is only used by SPs that need to access it, like the
    implementation of lambda, and get_current_environment.
    """

  def operandValues(self):
    """The actual arguments this SP is called with."""
    raise NotImplementedError

  def spaux(self):
    """The SP's saved auxiliary state."""
    raise NotImplementedError

  def madeSPAux(self):
    """The made SP's saved auxiliary state, if this is an AAA maker application."""
    raise NotImplementedError

  def esrValues(self):
    """The results of evaluation of requests the request stage made, if any."""
    raise NotImplementedError

  def esrNodes(self):
    """The identities of the evaluations of requests the request stage made, if any."""
    raise NotImplementedError

  def requestValue(self):
    """The request the requesting stage made, if any.  Rarely used."""
    raise NotImplementedError

  def py_prng(self):
    """PRNG with Python's standard `random.Random` interface that may be used.

    Mutable refence."""
    raise NotImplementedError

  def np_prng(self):
    """PRNG with Numpy's `RandomState` interface that may be used.

    Mutable reference."""
    raise NotImplementedError

class DeterministicPSP(PSP):
  """Provides good default implementations of PSP methods for deterministic
  PSPs."""

  @override(PSP) # type: ignore
  def isRandom(self):
    return False

  @override(PSP) # type: ignore
  def canAbsorb(self, _trace, _appNode, _parentNode):
    return False

  @override(PSP) # type: ignore
  def logDensity(self, _value, _args):
    return 0

  @override(PSP) # type: ignore
  def gradientOfLogDensity(self, _value, args):
    return (0, [0 for _ in args.operandNodes])

  @override(PSP) # type: ignore
  def logDensityBound(self, _value, _args): return 0

class DeterministicMakerAAAPSP(DeterministicPSP):
  """Provides good default implementations of PSP methods for PSPs that
  are deterministic makers whose children can absorb at applications.
  """

  def childrenCanAAA(self):
    return True

  def getAAALKernel(self):
    return DeterministicMakerAAALKernel(self)

class NullRequestPSP(DeterministicPSP):
  @override(DeterministicPSP) # type: ignore
  def simulate(self, _args):
    return Request()

  @override(PSP) # type: ignore
  def gradientOfSimulate(self, args, _value, _direction):
    return [0 for _ in args.operandNodes]

  @override(DeterministicPSP) # type: ignore
  def canAbsorb(self, _trace, _appNode, _parentNode):
    return True

class ESRRefOutputPSP(DeterministicPSP):
  @override(DeterministicPSP) # type: ignore
  def simulate(self, args):
    assert len(args.esrNodes()) ==  1
    return args.esrValues()[0]

  @override(PSP) # type: ignore
  def gradientOfSimulate(self, args, _value, direction):
    return [0 for _ in args.operandNodes] + [direction]

  @override(DeterministicPSP) # type: ignore
  def gradientOfLogDensity(self, _value, args):
    return (0, [0 for _ in args.operandNodes + args.esrNodes()])

  @override(DeterministicPSP) # type: ignore
  def canAbsorb(self,trace,appNode,parentNode):
    return parentNode != trace.esrParentsAt(appNode)[0] \
        and parentNode != appNode.requestNode

class RandomPSP(PSP):
  """Provides good default implementations of (two) PSP methods for
  (assessable) stochastic PSPs.
  """
  @override(PSP) # type: ignore
  def isRandom(self):
    return True

  @override(PSP) # type: ignore
  def canAbsorb(self, _trace, _appNode, _parentNode):
    return True

class LikelihoodFreePSP(RandomPSP):
  """Provides good default implementations of (two) PSP methods for
  likelihood-free stochastic PSPs.
  """
  @override(PSP) # type: ignore
  def canAbsorb(self, _trace, _appNode, _parentNode):
    return False

class TypedPSP(PSP):
  """Wrapper that implements the PSP interface by marshalling and
  unmarshalling according to a type signature, delegating to an
  internal PSP.

  The interface offered to the delegate of this class has all the same
  methods as the PSP interface, with all the same semantics, except
  that the values being operated upon and returned are native Python
  objects rather than Venture Values.
  TODO: Perhaps delegates of TypedPSP should not be subclasses of PSP,
  but of another base class named something like PythonPSP.
  """

  def __init__(self, psp, f_type):
    """The first argument is the PSP-like delegate, that is expected to
    do all the work, operating on Python representations of the data.

    The second argument is the type signature, which controls the
    marshalling and unmarshalling.  The type signature itself must be
    an instance of venture.lite.sp.SPType, and those are built
    predominantly out of instances of (subclasses of)
    venture.lite.types.VentureType.  See also the "Types" section
    of doc/type-system.md.

    """
    self.f_type = f_type
    self.psp = psp

  def __repr__(self):
    return 'TypedPSP(%r, %r)' % (self.psp, self.f_type)

  def simulate(self,args):
    return self.f_type.wrap_return(
      self.psp.simulate(self.f_type.unwrap_args(args)))

  def gradientOfSimulate(self, args, value, direction):
    # TODO Should gradientOfSimulate unwrap the direction and wrap the
    # answers using the gradient_type, like gradientOfLogDensity does?
    # Or do I want to use the vector space structure of gradients
    # given by the Venture values inside the Python methods?
    return self.psp.gradientOfSimulate(
      self.f_type.unwrap_args(args), self.f_type.unwrap_return(value), direction)

  def logDensity(self, value, args):
    return self.psp.logDensity(
      self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))

  def gradientOfLogDensity(self, value, args):
    (dvalue, dargs) = self.psp.gradientOfLogDensity(
      self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
    dvalue_wrapped = self.f_type.gradient_type().wrap_return(dvalue)
    if dargs is 0:
      dargs_wrapped = [0] * len(args.operandValues())
    else:
      dargs_wrapped = self.f_type.gradient_type().wrap_arg_list(dargs)
    return (dvalue_wrapped, dargs_wrapped)

  def logDensityBound(self, value, args):
    return self.psp.logDensityBound(
      self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))

  def incorporate(self, value, args):
    return self.psp.incorporate(self.f_type.unwrap_return(value),
      self.f_type.unwrap_args(args))

  def unincorporate(self, value, args):
    return self.psp.unincorporate(self.f_type.unwrap_return(value),
      self.f_type.unwrap_args(args))

  def logDensityOfData(self, aux):
    return self.psp.logDensityOfData(aux)

  def enumerateValues(self, args):
    return [self.f_type.wrap_return(v) for v in
        self.psp.enumerateValues(self.f_type.unwrap_args(args))]

  def isRandom(self):
    return self.psp.isRandom()

  def canAbsorb(self, trace, appNode, parentNode):
    return self.psp.canAbsorb(trace, appNode, parentNode)

  def childrenCanAAA(self):
    return self.psp.childrenCanAAA()

  def getAAALKernel(self):
    return TypedLKernel(self.psp.getAAALKernel(), self.f_type)

  def canEnumerate(self):
    return self.psp.canEnumerate()

  def hasVariationalLKernel(self): return self.psp.hasVariationalLKernel()

  def getVariationalLKernel(self, args):
    return TypedVariationalLKernel(self.psp.getVariationalLKernel(
      self.f_type.unwrap_args(args)), self.f_type)

  def hasSimulationKernel(self):
    return self.psp.hasSimulationKernel()

  def hasDeltaKernel(self):
    return self.psp.hasDeltaKernel()

  def getDeltaKernel(self, args):
    return TypedLKernel(self.psp.getDeltaKernel(args), self.f_type)
  # TODO Wrap the simulation and delta kernels properly (once those are tested)

  def description(self,name):
    type_names = self.f_type.names()
    signature = "\n".join(["%s :: %s" % (name, variant) for variant in type_names])
    return signature + "\n" + self.psp.description(name)

  def description_rst_format(self, name):
    signature = ".. function:: " + self.f_type.name_rst_format(name)
    return (signature, self.psp.description(name))

class DispatchingPSP(PSP):
  def __init__(self, f_types, psps):
    self.f_types = f_types
    self.psps = psps
    self.f_type = f_types[0] # TODO Hack to pacify SP.venture_type for now

  def _disptach(self, args):
    for (f_type, psp) in zip(self.f_types, self.psps):
      if f_type.args_match(args):
        return psp
    return self.psps[0] # And hope coersion succeeds

  def simulate(self, args):
    return self._disptach(args).simulate(args)

  def gradientOfSimulate(self, args, value, direction):
    return self._disptach(args).gradientOfSimulate(args, value, direction)

  def logDensity(self, value, args):
    return self._disptach(args).logDensity(value, args)

  def gradientOfLogDensity(self, value, args):
    return self._disptach(args).gradientOfLogDensity(value, args)

  def logDensityBound(self, value, args):
    return self._disptach(args).logDensityBound(value, args)

  def incorporate(self, value, args):
    return self._disptach(args).incorporate(value, args)

  def unincorporate(self, value, args):
    return self._disptach(args).unincorporate(value, args)

  def enumerateValues(self, args):
    return self._disptach(args).enumerateValues(args)

  # Is this really the right treatment of methods that don't give args?
  def logDensityOfData(self, aux):
    return self.psps[0].logDensityOfData(aux)

  def isRandom(self):
    return self.psps[0].isRandom()

  def canAbsorb(self, trace, appNode, parentNode):
    return self.psps[0].canAbsorb(trace, appNode, parentNode)

  def childrenCanAAA(self):
    return self.psps[0].childrenCanAAA()

  def getAAALKernel(self):
    return self.psps[0].getAAALKernel()

  def canEnumerate(self):
    return self.psps[0].canEnumerate()

  def hasVariationalLKernel(self):
    return self.psps[0].hasVariationalLKernel()

  def getVariationalLKernel(self, args):
    return self._disptach(args).getVariationalLKernel(args)

  def hasSimulationKernel(self):
    return self.psps[0].hasSimulationKernel()

  def hasDeltaKernel(self):
    return self.psps[0].hasDeltaKernel()

  def getDeltaKernel(self, args):
    return self._disptach(args).getDeltaKernel(args)

  def description(self, name):
    return self.psps[0].description(name)

  def description_rst_format(self, name):
    return self.psps[0].description_rst_format(name)

class TypedLKernel(LKernel):
  def __init__(self, kernel, f_type):
    self.kernel = kernel
    self.f_type = f_type

  def __repr__(self):
    return 'TypedLKernel(%r, %r)' % (self.kernel, self.f_type)

  def forwardSimulate(self, trace, oldValue, args):
    return self.f_type.wrap_return(self.kernel.forwardSimulate(
      trace, self.f_type.unwrap_return(oldValue), self.f_type.unwrap_args(args)))

  def forwardWeight(self, trace, newValue, oldValue, args):
    return self.kernel.forwardWeight(trace, self.f_type.unwrap_return(newValue),
      self.f_type.unwrap_return(oldValue), self.f_type.unwrap_args(args))

  def reverseWeight(self, trace, oldValue, args):
    return self.kernel.reverseWeight(trace, self.f_type.unwrap_return(oldValue),
      self.f_type.unwrap_args(args))

  def gradientOfReverseWeight(self, trace, value, args):
    (dvalue, dargs) = self.kernel.gradientOfReverseWeight(trace,
      self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))
    dvalue_wrapped = self.f_type.gradient_type().wrap_return(dvalue)
    if dargs is 0:
      dargs_wrapped = [0] * len(args.operandValues())
    else:
      dargs_wrapped = self.f_type.gradient_type().wrap_arg_list(dargs)
    return (dvalue_wrapped, dargs_wrapped)

  def weightBound(self, trace, value, args):
    return self.kernel.weightBound(trace, self.f_type.unwrap_return(value),
      self.f_type.unwrap_args(args))

class TypedVariationalLKernel(TypedLKernel):
  def gradientOfLogDensity(self, value, args):
    return self.kernel.gradientOfLogDensity(
      self.f_type.unwrap_return(value), self.f_type.unwrap_args(args))

  def updateParameters(self, gradient, gain, stepSize):
    return self.kernel.updateParameters(gradient, gain, stepSize)
