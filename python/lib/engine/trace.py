# Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.

import copy

import venture.value.dicts as v
from venture.exception import VentureException

class Trace(object):
  """Defines all the methods that do the actual work of interacting with
  the backend-specific traces.

  """
  def __init__(self, trace, directives=None, foreign_sp_names=None):
    assert not isinstance(trace, Trace) # I've had too many double-wrapping bugs
    self.trace = trace
    if directives is not None:
      self.directives = copy.copy(directives)
    else:
      self.directives = {}
    # TODO Do I want to turn this into part of the directive list?
    # That way, can interleave binding with other directives; possibly
    # forget imports
    if foreign_sp_names is not None:
      self.foreign_sp_names = copy.copy(foreign_sp_names)
    else:
      self.foreign_sp_names = set()

  def __getattr__(self, attrname):
    # Forward all other trace methods without modification
    return getattr(self.trace, attrname)

  def define(self, baseAddr, id, exp):
    assert baseAddr not in self.directives
    self.trace.eval(baseAddr, exp)
    self.trace.bindInGlobalEnv(id, baseAddr)
    self.directives[baseAddr] = ["define", id, exp]
    return self.trace.extractValue(baseAddr)

  def evaluate(self, baseAddr, exp):
    assert baseAddr not in self.directives
    self.trace.eval(baseAddr,exp)
    self.directives[baseAddr] = ["evaluate", exp]
    return self.trace.extractValue(baseAddr)

  def observe(self, baseAddr, exp, val):
    assert baseAddr not in self.directives
    self.trace.eval(baseAddr, exp)
    logDensity = self.trace.observe(baseAddr,val)
    if logDensity == float("-inf"):
      raise VentureException("invalid_constraint", "Observe failed to constrain",
                             expression=exp, value=val)
    self.directives[baseAddr] = ["observe", exp, val]

  def forget(self, directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot forget a non-existent directive id.  Valid options are %s" % self.directives.keys(),
                             argument="directive_id", directive_id=directiveId)
    directive = self.directives[directiveId]
    if directive[0] == "observe": self.trace.unobserve(directiveId)
    self.trace.uneval(directiveId)
    if directive[0] == "define": self.trace.unbindInGlobalEnv(directive[1])
    del self.directives[directiveId]

  def freeze(self, directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot freeze a non-existent directive id.  Valid options are %s" % self.directives.keys(),
                             argument="directive_id", directive_id=directiveId)
    self.trace.freeze(directiveId)
    self._record_directive_frozen(directiveId)

  def _record_directive_frozen(self, directiveId):
    # TODO This update will needlessly prevent freezing procedure assumes.
    value = self.trace.extractValue(directiveId)
    directive = self.directives[directiveId]
    if directive[0] == "define":
      self.directives[directiveId] = ["define", directive[1], v.quote(value)]
    elif directive[0] == "observe":
      self.directives[directiveId] = ["observe", v.quote(value), directive[2]]
    elif directive[0] == "evaluate":
      self.directives[directiveId] = ["evaluate", v.quote(value)]
    else:
      assert False, "Impossible directive type %s detected" % directive[0]

  def report_value(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument", "Cannot report a non-existent directive id",
                             argument=directiveId)
    return self.trace.extractValue(directiveId)

  def report_raw(self,directiveId):
    if directiveId not in self.directives:
      raise VentureException("invalid_argument",
                             "Cannot report raw value of a non-existent directive id",
                             argument=directiveId)
    return self.trace.extractRaw(directiveId)

  def bind_foreign_sp(self, name, sp):
    # Assume the SP came from the engine's foreign SP registry
    self.foreign_sp_names.add(name)
    self.trace.bindPrimitiveSP(name, sp)

  def reset_to_prior(self):
    """Unincorporate all observations and return to the prior.

(By forgetting and then replaying the stored directives with no
inference.)

    """
    # Note: In principle it is possible to reset_to_prior by throwing
    # the existing trace away bodily, creating an empty one, and
    # replaying the directives, instead of keeping the existing trace
    # but forgetting everything the way this does.  That would save
    # work if there are more directives to forget than there would be
    # global environment symbols to rebind.  However, implementing
    # this requires self to have access to the backend-specific Trace
    # constructor, and the bound foreign SPs, which is why I didn't do
    # it that way.  Also, Puma trace reconstruction eits the RNG (as
    # of this writing), so it would need to be reset; whereas the
    # present approach doesn't have that problem.
    worklist = sorted(self.directives.iteritems())
    for (did, _) in reversed(worklist):
      self.forget(did)
    for (did, directive) in worklist:
      getattr(self, directive[0])(did, *directive[1:])

  def diversify(self, exp, copy_trace):
    def copy_inner_trace(trace):
      assert trace is self.trace
      return copy_trace(self).trace
    (traces, weights) = self.trace.diversify(exp, copy_inner_trace)
    return ([Trace(t, self.directives) for t in traces], weights)

  def dump(self, skipStackDictConversion=False):
    values = _dump_trace(self.trace, self.directives, skipStackDictConversion)
    return (values, self.directives, self.foreign_sp_names)

  @staticmethod
  def restore(mk_trace, serialized, foreign_sps, skipStackDictConversion=False):
    (values, directives, foreign_sp_names) = serialized
    return Trace(_restore_trace(mk_trace(), directives, values, foreign_sp_names, foreign_sps, skipStackDictConversion), directives, foreign_sp_names)

  def stop_and_copy(self):
    return Trace(self.trace.stop_and_copy(), self.directives)

######################################################################
# Auxiliary functions for dumping and loading backend-specific traces
######################################################################

def _dump_trace(trace, directives, skipStackDictConversion=False):
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
  # trace originally had.  In the absence of tracking that, this
  # heuristically makes the trace fully incorporated.  Hopefully,
  # mistakes will be rarer than in the past (which will make them even
  # harder to detect).
  trace.registerConstraints()

  return trace.dumpSerializationDB(db, skipStackDictConversion)

def _restore_trace(trace, directives, values, foreign_sp_names, foreign_sps, skipStackDictConversion=False):
  # Bind the foreign sps; wrap if necessary
  for name in foreign_sp_names:
    trace.bindPrimitiveSP(name, foreign_sps[name])

  db = trace.makeSerializationDB(values, skipStackDictConversion)

  for did, directive in sorted(directives.items()):
    if directive[0] == "define":
      name, datum = directive[1], directive[2]
      trace.evalAndRestore(did, datum, db)
      trace.bindInGlobalEnv(name, did)
    elif directive[0] == "observe":
      datum, val = directive[1], directive[2]
      trace.evalAndRestore(did, datum, db)
      trace.observe(did, val)
    elif directive[0] == "evaluate":
      datum = directive[1]
      trace.evalAndRestore(did, datum, db)

  # TODO Actually, I should restore the degree of incorporation the
  # original trace had.  In the absence of tracking that, this
  # heuristically makes the trace fully incorporated.  Hopefully,
  # mistakes will be rarer than in the past (which will make them even
  # harder to detect).
  trace.registerConstraints()
  

  return trace
