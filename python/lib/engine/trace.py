from venture.engine.utils import expToDict
from venture.exception import VentureException

class Trace(object):
  """Defines all the methods that do the actual work of interacting with
  the backend-specific traces.

  """
  def __init__(self, trace): self.trace = trace

  def __getattr__(self, attrname):
    # Forward all other trace methods without modification
    return getattr(self.trace, attrname)

  def assume(self, baseAddr, id, exp):
    self.trace.eval(baseAddr, exp)
    self.trace.bindInGlobalEnv(id, baseAddr)
    return self.trace.extractValue(baseAddr)

  def predict_all(self, baseAddr, datum):
    self.trace.eval(baseAddr,datum)
    return self.trace.extractValue(baseAddr)

  def observe(self, baseAddr, datum, val):
    self.trace.eval(baseAddr, datum)
    logDensity = self.trace.observe(baseAddr,val)
    # TODO check for -infinity? Throw an exception?
    if logDensity == float("-inf"):
      raise VentureException("invalid_constraint", "Observe failed to constrain",
                             expression=datum, value=val)

  def forget(self, directive, directiveId):
    if directive[0] == "observe": self.trace.unobserve(directiveId)
    self.trace.uneval(directiveId)
    if directive[0] == "assume": self.trace.unbindInGlobalEnv(directive[1])

  def freeze(self, directiveId):
    self.trace.freeze(directiveId)

  def bind_foreign_sp(self, name, sp):
    self.trace.bindPrimitiveSP(name, sp)

  def primitive_infer(self, exp):
    if hasattr(self.trace, "infer_exp"):
      # The trace can handle the inference primitive syntax natively
      self.trace.infer_exp(exp)
    else:
      # The trace cannot handle the inference primitive syntax
      # natively, so translate.
      d = expToDict(exp)
      #import pdb; pdb.set_trace()
      self.trace.infer(d)
