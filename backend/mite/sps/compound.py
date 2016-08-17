from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError

from venture.mite.sp import VentureSP

class CompoundSP(VentureSP):
  def __init__(self, params, exp, env):
    super(CompoundSP, self).__init__()
    self.params = params
    self.exp = exp
    self.env = env

  def apply(self, trace_handle, application_id, inputs):
    if len(self.params) != len(inputs):
      raise VentureError("Wrong number of arguments: " \
        "compound takes exactly %d arguments, got %d." \
        % (len(self.params), len(inputs)))
    extendedEnv = VentureEnvironment(self.env, self.params, inputs)
    addr = trace_handle.request_address(application_id)
    result = trace_handle.eval_request(
      addr, self.exp, extendedEnv)
    return result

  def unapply(self, trace_handle, application_id, _output, _inputs):
    addr = trace_handle.request_address(application_id)
    trace_handle.uneval_request(addr)
    return None

  def restore(self, trace_handle, application_id, _inputs, _frag):
    addr = trace_handle.request_address(application_id)
    result = trace_handle.restore_request(addr)
    return result
