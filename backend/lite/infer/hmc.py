import numpy.random as npr
import scipy.stats
from ..omegadb import OmegaDB
from ..regen import regenAndAttach
from ..detach import detachAndExtract
from ..scaffold import constructScaffold
from ..utils import FixedRandomness
from ..value import vv_dot_product
from mh import InPlaceOperator, getCurrentValues, registerDeterministicLKernels

class GradientOfRegen(object):
  """An applicable object, calling which computes the gradient
  of regeneration along the given scaffold.  Also permits performing
  one final such regeneration without computing the gradient.  The
  value of this class is that it supports repeated regenerations (and
  gradient computations), and that it preserves the randomness across
  said regenerations (enabling gradient methods to be applied
  sensibly)."""

  # Much disastrous hackery is necessary to implement this because
  # both regen and detach mutate the scaffold (!) and regen depends
  # upon the scaffold having been detached along.  However, each new
  # regen potentially creates new brush, which has to be traversed by
  # the following corresponding detach in order to compute the
  # gradient.  So if I am going to detach and regen repeatedly, I need
  # to pass the scaffolds from one to the next and rebuild them
  # properly.
  def __init__(self, trace, scaffold, pnodes):
    self.trace = trace
    self.scaffold = scaffold
    # Pass and store the pnodes because their order matters, and the
    # scaffold has them as a set
    self.pnodes = pnodes
    self.fixed_randomness = FixedRandomness()

  def __call__(self, values):
    """Returns the gradient of the weight of regenerating along
    an (implicit) scaffold starting with the given values.  Smashes
    the trace, but leaves it a torus.  Assumes there are no delta
    kernels around."""
    # TODO Assert that no delta kernels are requested?
    self.fixed_regen(values)
    new_scaffold = constructScaffold(self.trace, [set(self.pnodes)])
    registerDeterministicLKernels(self.trace, new_scaffold, self.pnodes, values)
    (_, rhoDB) = detachAndExtract(self.trace, new_scaffold, True)
    self.scaffold = new_scaffold
    return [rhoDB.getPartial(pnode) for pnode in self.pnodes]

  def fixed_regen(self, values):
    # Ensure repeatability of randomness
    with self.fixed_randomness:
      return self.regen(values)

  def regen(self, values):
    registerDeterministicLKernels(self.trace, self.scaffold, self.pnodes, values)
    return regenAndAttach(self.trace, self.scaffold, False, OmegaDB(), {})


class HamiltonianMonteCarloOperator(InPlaceOperator):

  def __init__(self, epsilon, L):
    self.epsilon = epsilon
    self.num_steps = L

  # Notionally, I want to do Hamiltonian Monte Carlo on the potential
  # given by this function:
  #   def potential(values):
  #     registerDeterministicLKernels(trace,scaffold,pnodes,values)
  #     return -regenAndAttach(trace, scaffold, False, OmegaDB(), {})
  #
  # The trouble, of course, is that I need the gradient of this to
  # actually do HMC.
  #
  # I don't trust any of Python's extant AD libraries to get this
  # right, so I'm going to do it by implementing one level of reverse
  # mode AD myself.  Fortunately, the trace acts like a tape already.
  # Unfortunately, regen constitutes the forward phase but has no
  # reverse phase.  Fortunately, detach traverses the trace in the
  # proper order so can compute the reverse phase.  Unfortunately,
  # detach mutates the trace as it goes, so there will be some
  # machinations (perhaps I should use particles?)

  def propose(self, trace, scaffold):
    pnodes = scaffold.getPrincipalNodes()
    currentValues = getCurrentValues(trace,pnodes)

    # So the initial detach will get the gradient right
    registerDeterministicLKernels(trace, scaffold, pnodes, currentValues)
    rhoWeight = self.prepare(trace, scaffold, True) # Gradient is in self.rhoDB

    momenta = self.sampleMomenta(currentValues)
    start_K = self.kinetic(momenta)

    grad = GradientOfRegen(trace, scaffold, pnodes)
    def grad_potential(values):
      # The potential function we want is - log density
      return [-dx for dx in grad(values)]

    # Might as well save a gradient computation, since the initial
    # detach does it
    start_grad_pot = [-self.rhoDB.getPartial(pnode) for pnode in pnodes]

    # Smashes the trace but leaves it a torus
    (proposed_values, end_K) = self.evolve(grad_potential, currentValues, start_grad_pot, momenta)

    xiWeight = grad.regen(proposed_values) # Mutates the trace
    # The weight arithmetic is given by the Hamiltonian being
    # -weight + kinetic(momenta)
    return (trace, xiWeight - rhoWeight + start_K - end_K)

  def sampleMomenta(self, currentValues):
    def sample_normal(_):
      return scipy.stats.norm.rvs(loc=0, scale=1)
    return [v.map_real(sample_normal) for v in currentValues]
  def kinetic(self, momenta):
    # This is the log density of sampling these momenta, up to an
    # additive constant
    return sum([vv_dot_product(m, m) for m in momenta]) / 2.0

  def evolve(self, grad_U, start_q, start_grad_q, start_p):
    epsilon = self.epsilon
    num_steps = npr.randint(int(self.num_steps))+1
    q = start_q
    # The initial momentum half-step
    dpdt = start_grad_q
    p = [pi - dpdti * (epsilon / 2.0) for (pi, dpdti) in zip(start_p, dpdt)]

    for i in range(num_steps):
      # Position step
      q = [qi + pi * epsilon for (qi, pi) in zip(q,p)]

      # Momentum step, except at the end
      if i < num_steps - 1:
        dpdt = grad_U(q)
        p = [pi - dpdti * epsilon for (pi, dpdti) in zip(p, dpdt)]

    # The final momentum half-step
    dpdt = grad_U(q)
    p = [pi - dpdti * (epsilon / 2.0) for (pi, dpdti) in zip(p, dpdt)]

    # Negate momenta at the end to make the proposal symmetric
    # (irrelevant if the kinetic energy function is symmetric)
    p = [-pi for pi in p]

    return q, self.kinetic(p)

  def name(self): return "hamiltonian monte carlo"
