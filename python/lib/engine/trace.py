import venture.lite.foreign as foreign
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

  def define(self, baseAddr, id, exp):
    self.trace.eval(baseAddr, exp)
    self.trace.bindInGlobalEnv(id, baseAddr)
    return self.trace.extractValue(baseAddr)

  def evaluate(self, baseAddr, datum):
    self.trace.eval(baseAddr,datum)
    return self.trace.extractValue(baseAddr)

  def observe(self, baseAddr, datum, val):
    self.trace.eval(baseAddr, datum)
    logDensity = self.trace.observe(baseAddr,val)
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

  def diversify(self, exp, copy_trace):
    def copy_inner_trace(trace):
      assert trace is self.trace
      return copy_trace(self).trace
    (traces, weights) = self.trace.diversify(exp, copy_inner_trace)
    return ([Trace(t) for t in traces], weights)

  def dump(self, directives, skipStackDictConversion=False):
    return _dump_trace(self.trace, directives, skipStackDictConversion)

  @staticmethod
  def restore(engine, values, skipStackDictConversion=False):
    return Trace(_restore_trace(engine.Trace(), engine.directives, values, engine.foreign_sps, engine.name, skipStackDictConversion))

######################################################################
# Auxiliary functions for dumping and loading backend-specific traces
######################################################################

def _dump_trace(trace, directives, skipStackDictConversion=False):
  # TODO: It would be good to pass foreign_sps to this function as well,
  # and then check that the passed foreign_sps match up with the foreign
  # SP's bound in the trace's global environment. However, in the Puma backend
  # there is currently no way to access this global environment.
  # This block mutates the trace
  db = trace.makeSerializationDB()
  for did, directive in sorted(directives.items(), reverse=True):
    if directive[0] == "observe":
      trace.unobserve(did)
    trace.unevalAndExtract(did, db)

  # This block undoes the mutation on the trace done by the previous block; but
  # it does not destroy the value stack because the actual OmegaDB (superclass
  # of OrderedOmegaDB) has the values.
  for did, directive in sorted(directives.items()):
    trace.restore(did, db)
    if directive[0] == "observe":
      trace.observe(did, directive[2])

  # TODO Actually, I should restore the degree of incorporation the
  # original trace had.  In the absence of tracking that, this
  # heuristically makes the trace fully incorporated.  Hopefully,
  # mistakes will be rarer than in the past (which will make them even
  # harder to detect).
  trace.makeConsistent()

  return trace.dumpSerializationDB(db, skipStackDictConversion)

def _restore_trace(trace, directives, values, foreign_sps,
                   backend, skipStackDictConversion=False):
  # bind the foreign sp's; wrap if necessary
  for name, sp in foreign_sps.items():
    if backend != 'lite':
      sp = foreign.ForeignLiteSP(sp)
    trace.bindPrimitiveSP(name, sp)

  db = trace.makeSerializationDB(values, skipStackDictConversion)

  for did, directive in sorted(directives.items()):
      if directive[0] == "assume":
          name, datum = directive[1], directive[2]
          trace.evalAndRestore(did, datum, db)
          trace.bindInGlobalEnv(name, did)
      elif directive[0] == "observe":
          datum, val = directive[1], directive[2]
          trace.evalAndRestore(did, datum, db)
          trace.observe(did, val)
      elif directive[0] == "predict":
          datum = directive[1]
          trace.evalAndRestore(did, datum, db)

  return trace
