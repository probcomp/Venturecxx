from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError

from venture.mite.sp import RequestReferenceSP

class CompoundSP(RequestReferenceSP):
  def __init__(self, params, exp, env):
    super(CompoundSP, self).__init__()
    self.params = params
    self.exp = exp
    self.env = env

  def request(self, trace_handle, application_id, inputs):
    if len(self.params) != len(inputs):
      raise VentureError("Wrong number of arguments: " \
        "compound takes exactly %d arguments, got %d." \
        % (len(self.params), len(inputs)))
    raddr = application_id
    extendedEnv = VentureEnvironment(self.env, self.params, inputs)
    trace_handle.new_request(raddr, self.exp, extendedEnv)
    return raddr
