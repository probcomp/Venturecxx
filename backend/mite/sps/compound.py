from venture.lite.env import VentureEnvironment
from venture.lite.exception import VentureError

from venture.mite.sp import RequestReferenceSP

class CompoundSP(RequestReferenceSP):
  def __init__(self, params, exp, env):
    super(CompoundSP, self).__init__()
    self.params = params
    self.exp = exp
    self.env = env

  def request(self, args):
    if len(self.params) != len(args.operandNodes):
      raise VentureError("Wrong number of arguments: " \
        "compound takes exactly %d arguments, got %d." \
        % (len(self.params), len(args.operandNodes)))
    raddr = args.node
    extendedEnv = VentureEnvironment(self.env, self.params, args.operandNodes)
    args.newRequest(raddr, self.exp, extendedEnv)
    return raddr
