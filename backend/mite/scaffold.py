from collections import OrderedDict

import venture.mite.address as addresses
from venture.mite.sp import ApplicationKernel

class MinimalScaffold(object):
  def __init__(self, kernels):
    # address -> kernel or kernel selector
    self.kernels = kernels

  def kernel_at(self, sp, trace_handle, address):
    kernel = self.kernels.get(address)
    if isinstance(kernel, ApplicationKernel):
      return kernel
    elif kernel is None:
      return None
    elif kernel['type'] == 'proposal':
      return sp.proposal_kernel(trace_handle, address)
    elif kernel['type'] == 'constrained':
      val = kernel['val']
      return sp.constrained_kernel(trace_handle, address, val)

class DefaultAllScaffold(object):
  def kernel_at(self, sp, trace_handle, address):
    return sp.proposal_kernel(trace_handle, address)



def single_site_scaffold(trace, principal_address):
  # lightweight implementation to find a single-site scaffold.
  # very brittle and doesn't work on requests at all, for now.

  # TODO: one way to make this work on requests might be to do a full
  # extract-restore pass through the program and intercept the
  # requests it makes.

  kernels = OrderedDict()
  affected = set()

  def traverse(addr, exp, env):
    import venture.lite.exp as e
    if e.isVariable(exp):
      result_node = env.findSymbol(exp)
      if result_node.address in affected:
        kernels[addr] = {'type': 'propagate_lookup'}
        affected.add(addr)
    elif (e.isSelfEvaluating(exp) or
          e.isQuotation(exp) or
          e.isLambda(exp)):
      pass
    else:
      # SP application
      parents_affected = []
      for index, subexp in enumerate(exp):
        subaddr = addresses.subexpression(index, addr)
        traverse(subaddr, subexp, env)
        parents_affected.append(subaddr in affected)
      if addr == principal_address:
        kernels[addr] = {'type': 'proposal'}
        affected.add(addr)
      elif parents_affected[0]:
        # operator changed
        kernels[addr] = {'type': 'proposal'}
        affected.add(addr)
      elif any(parents_affected[1:]):
        sp_ref = trace.value_at(addresses.subexpression(0, addr))
        sp = trace.deref_sp(sp_ref).value
        val = trace.value_at(addr)
        kernel = sp.constrained_kernel(None, addr, val)
        if kernel is NotImplemented or likelihood_free_lite_sp(sp):
          kernels[addr] = {'type': 'proposal'}
          affected.add(addr)
        else:
          kernels[addr] = {'type': 'constrained', 'val': val}

  def likelihood_free_lite_sp(sp):
    from venture.mite.sps.lite_sp import LiteSP
    if isinstance(sp, LiteSP):
      try:
        return not sp.wrapped_sp.outputPSP.canAbsorb(None, None, None)
      except:
        return True
    else:
      return False

  for i in range(trace.directive_counter):
    addr = addresses.directive(i+1)
    (exp, env) = trace.requests[addr]
    traverse(addr, exp, env)

  return MinimalScaffold(kernels)
