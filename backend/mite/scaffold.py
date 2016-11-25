from collections import OrderedDict

from venture.mite.sp import ApplicationKernel
import venture.mite.address as addresses

class Scaffold(object):
  def __init__(self, kernels):
    # address -> kernel or kernel selector
    self.kernels = kernels

  def kernel_at(self, sp, trace_handle, address):
    kernel = self.kernels.get(address)
    k = self._interpret_kernel(kernel, sp, trace_handle, address)
    self.kernels[address] = k
    return k

  def _interpret_kernel(self, kernel, sp, trace_handle, address):
    if isinstance(kernel, ApplicationKernel):
      return kernel
    elif kernel is None:
      return None
    elif isinstance(kernel, list):
      return SequenceKernel([self._interpret_kernel(k, sp, trace_handle, address) for k in kernel])
    elif kernel['type'] == 'proposal':
      return sp.proposal_kernel(trace_handle, address)
    elif kernel['type'] == 'constraint':
      val = kernel['val']
      return sp.constraint_kernel(trace_handle, address, val)
    elif kernel['type'] == 'propagate_request':
      parent = kernel['parent']
      return sp.propagating_kernel(trace_handle, address, parent)
    elif kernel['type'] == 'request_constraint':
      return sp.request_constraint_kernel(trace_handle, address)

class DefaultAllScaffold(object):
  def kernel_at(self, sp, trace_handle, address):
    return sp.proposal_kernel(trace_handle, address)

class SequenceKernel(ApplicationKernel):
  def __init__(self, subkernels):
    self.subkernels = subkernels

  def extract(self, output, inputs):
    # TODO What's the right backward chaining of intermediate outputs,
    # if there is one?  What about intermediate inputs?
    total = 0
    answer = []
    for k in reversed(self.subkernels):
      (w, sub_out) = k.extract(output, inputs)
      total += w
      answer.insert(0, sub_out)
    return (total, answer)

  def regen(self, inputs):
    total = 0
    answer = None
    for k in self.subkernels:
      (w, sub_out) = k.regen(inputs)
      total += w
      answer = sub_out
    return (total, answer)

  def restore(self, inputs, output):
    answer = None
    for (k, sub_out) in zip(self.subkernels, output):
      answer = k.restore(inputs, sub_out)
    return answer

def single_site_scaffold(trace, principal_address, principal_kernel=None):
  # lightweight implementation to find a single-site scaffold.
  # very brittle and doesn't work on requests at all, for now.

  # TODO: one way to make this work on requests might be to do a full
  # extract-restore pass through the program and intercept the
  # requests it makes.

  # If the input involved calls to `toplevel`, need to inject the ID
  # of the current trace.  Harmless otherwise.
  principal_address = addresses.interpret_address_in_trace(principal_address, trace.trace_id, None)

  kernels = OrderedDict()
  drg = set()

  if principal_kernel is None:
    principal_kernel = {'type': 'proposal'}

  def traverse(addr, exp, env):
    import venture.lite.exp as e
    if e.isVariable(exp):
      result_node = env.findSymbol(exp)
      if result_node.address in drg:
        kernels[addr] = {'type': 'propagate_lookup'}
        drg.add(addr)
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
        parents_affected.append(subaddr in drg)
      if addr == principal_address:
        # print "Proposing at", addr
        kernels[addr] = principal_kernel
        drg.add(addr)
      elif parents_affected[0]:
        # operator changed
        kernels[addr] = {'type': 'proposal'}
        drg.add(addr)
      elif any(parents_affected[1:]):
        if is_constrainable_application(addr):
          kernels[addr] = {'type': 'constraint', 'val': trace.value_at(addr)}
        else:
          kernels[addr] = {'type': 'proposal'}
          drg.add(addr)

  def is_constrainable_application(addr):
    sp_ref = trace.value_at(addresses.subexpression(0, addr))
    sp = trace.deref_sp(sp_ref).value
    val = trace.value_at(addr)
    kernel = sp.constraint_kernel(None, addr, val)
    if kernel is NotImplemented or likelihood_free_lite_sp(sp):
      return False
    else:
      return True

  def likelihood_free_lite_sp(sp):
    from venture.mite.sps.lite_sp import LiteSP
    if isinstance(sp, LiteSP):
      try:
        return not sp.wrapped_sp.outputPSP.canAbsorb(None, None, None)
      except Exception: # XXX Why is there a try-catch here anyway?
        return True
    else:
      return False

  for addr in trace.toplevel_addresses:
    (exp, env) = trace.requests[addr]
    traverse(addr, exp, env)

  return Scaffold(kernels)
