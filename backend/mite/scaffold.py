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
