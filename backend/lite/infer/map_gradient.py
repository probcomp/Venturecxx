import math
from ..lkernel import DeterministicLKernel
from mh import InPlaceOperator, getCurrentValues, registerDeterministicLKernels

class MAPOperator(InPlaceOperator):
  def __init__(self, epsilon, steps):
    self.epsilon = epsilon
    self.steps = steps

  def propose(self, trace, scaffold):
    pnodes = scaffold.getPrincipalNodes()
    currentValues = getCurrentValues(trace,pnodes)

    # So the initial detach will get the gradient right
    registerDeterministicLKernels(trace, scaffold, pnodes, currentValues)
    _rhoWeight = self.prepare(trace, scaffold, True) # Gradient is in self.rhoDB

    grad = GradientOfRegen(trace, scaffold, pnodes)

    # Might as well save a gradient computation, since the initial
    # detach does it
    start_grad = [self.rhoDB.getPartial(pnode) for pnode in pnodes]

    # Smashes the trace but leaves it a torus
    proposed_values = self.evolve(grad, currentValues, start_grad)

    _xiWeight = grad.regen(proposed_values) # Mutates the trace

    return (trace, 1000) # It's MAP -- try to force acceptance

  def evolve(self, grad, values, start_grad):
    xs = values
    dxs = start_grad
    for _ in range(self.steps):
      xs = [x + dx*self.epsilon for (x,dx) in zip(xs, dxs)]
      dxs = grad(xs)
    return xs

  def name(self): return "gradient ascent"

class NesterovAcceleratedGradientAscentOperator(MAPOperator):
  def step_lam(self, lam):
    return (1 + math.sqrt(1 + 4 * lam * lam))/2
  def gamma(self, lam):
    return (1 - lam) / self.step_lam(lam)
  def evolve(self, grad, values, start_grad):
    # This formula is from
    # http://blogs.princeton.edu/imabandit/2013/04/01/acceleratedgradientdescent/
    xs = values
    ys = xs
    dxs = start_grad
    lam = 1
    for _ in range(self.steps):
      gam = self.gamma(lam)
      new_ys = [x + dx*self.epsilon for (x,dx) in zip(xs, dxs)]
      new_xs = [old_y * gam + new_y * (1-gam) for (old_y, new_y) in zip(ys, new_ys)]
      (xs, ys, dxs, lam) = (new_ys, new_ys, grad(new_xs), self.step_lam(lam))
    return xs
  def name(self): return "gradient ascent with Nesterov acceleration"