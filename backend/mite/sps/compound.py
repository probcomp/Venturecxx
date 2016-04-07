from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError

from venture.mite.sp import RequestReferenceSP

class CompoundSP(RequestReferenceSP):
  def __init__(self, params, exp, env, addr):
    super(CompoundSP, self).__init__()
    self.params = params
    self.exp = exp
    self.env = env
    self.addr = addr

  def request(self, args):
    if len(self.params) != len(args.operandNodes):
      raise VentureError("Wrong number of arguments: " \
        "compound takes exactly %d arguments, got %d." \
        % (len(self.params), len(args.operandNodes)))
    extendedEnv = VentureEnvironment(self.env, self.params, args.operandNodes)
    return args.request(self.exp, extendedEnv, self.addr)
