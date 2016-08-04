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
    result = trace_handle.new_request(
      application_id, self.exp, extendedEnv)
    return trace_handle.value_at(result)

  def unapply(self, trace_handle, application_id, _output, _inputs):
    trace_handle.free_request(application_id)
    return None

  def restore(self, trace_handle, application_id, _inputs, _frag):
    trace_handle.restore_request(application_id)
    return trace_handle.value_at(application_id)
