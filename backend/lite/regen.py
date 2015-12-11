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

import numbers

from venture.exception import VentureException
from venture.lite.consistency import assertTorus
from venture.lite.consistency import assertTrace
from venture.lite.exception import VentureError
from venture.lite.exception import VentureNestedRiplMethodError
from venture.lite.lkernel import VariationalLKernel
from venture.lite.node import isConstantNode
from venture.lite.node import isLookupNode
from venture.lite.node import isOutputNode
from venture.lite.node import isRequestNode
from venture.lite.psp import NullRequestPSP
from venture.lite.psp import PSP
from venture.lite.scope import isTagOutputPSP
from venture.lite.sp import VentureSPRecord
from venture.lite.value import SPRef
import venture.lite.exp as e

def regenAndAttach(trace,scaffold,shouldRestore,omegaDB,gradients):
  assertTorus(scaffold)
  assert len(scaffold.border) == 1
  ans = regenAndAttachAtBorder(trace, scaffold.border[0], scaffold, shouldRestore, omegaDB, gradients)
  assertTrace(trace, scaffold)
  return ans

def regenAndAttachAtBorder(trace,border,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  constraintsToPropagate = {}
  for node in border:
#    print "regenAndAttach...",node
    if scaffold.isAbsorbing(node):
      weight += attach(trace,node,scaffold,shouldRestore,omegaDB,gradients)
    else:
      weight += regen(trace,node,scaffold,shouldRestore,omegaDB,gradients)
      if node.isObservation:
        weight += getAndConstrain(trace,node,constraintsToPropagate)
  propagateConstraints(trace,constraintsToPropagate)

  assert isinstance(weight, numbers.Number)
  return weight

def getAndConstrain(trace,node,constraintsToPropagate):
  appNode = trace.getConstrainableNode(node)
  weight = constrain(trace,appNode,node.observedValue)
  constraintsToPropagate[appNode] = node.observedValue
  return weight

def constrain(trace,node,value):
  psp,args = trace.pspAt(node),trace.argsAt(node)
  psp.unincorporate(trace.valueAt(node),args)
  weight = psp.logDensity(value,args)
  trace.setValueAt(node,value)
  psp.incorporate(value,args)
  trace.registerConstrainedChoice(node)
  assert isinstance(weight, numbers.Number)
  return weight

def propagateConstraints(trace,constraintsToPropagate):
  for node,value in constraintsToPropagate.iteritems():
    for child in trace.childrenAt(node):
      propagateConstraint(trace,child,value)

def propagateConstraint(trace,node,value):
  if isLookupNode(node): trace.setValueAt(node,value)
  elif isRequestNode(node):
    if not isinstance(trace.pspAt(node),NullRequestPSP):
      raise VentureException("evaluation", "Cannot make requests downstream of a node that gets constrained during regen", address = node.address)
  else:
    # TODO there may be more cases to ban here.
    # e.g. certain kinds of deterministic coupling through mutation.
    assert isOutputNode(node)
    if trace.pspAt(node).isRandom():
      raise VentureException("evaluation", "Cannot make random choices downstream of a node that gets constrained during regen", address = node.address)
    # TODO Is it necessary to unincorporate and incorporate here?  If
    # not, why not?
    trace.setValueAt(node,trace.pspAt(node).simulate(trace.argsAt(node)))
  for child in trace.childrenAt(node): propagateConstraint(trace,child,value)

def attach(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients)
  weight += absorb(trace, node)
  return weight

def absorb(trace, node):
  psp,args,gvalue = trace.pspAt(node),trace.argsAt(node),trace.groundValueAt(node)
  weight = psp.logDensity(gvalue,args)
  psp.incorporate(gvalue,args)
  assert isinstance(weight, numbers.Number)
  return weight

def regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  for parent in trace.definiteParentsAt(node): weight += regen(trace,parent,scaffold,shouldRestore,omegaDB,gradients)
  for parent in trace.esrParentsAt(node): weight += regen(trace,parent,scaffold,shouldRestore,omegaDB,gradients)
  assert isinstance(weight, numbers.Number)
  return weight

def regenESRParents(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  for parent in trace.esrParentsAt(node): weight += regen(trace,parent,scaffold,shouldRestore,omegaDB,gradients)
  assert isinstance(weight, numbers.Number)
  return weight

def regen(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  if scaffold.isResampling(node):
    if trace.regenCountAt(scaffold,node) == 0:
      weight += regenParents(trace,node,scaffold,shouldRestore,omegaDB,gradients)
      if isLookupNode(node):
        propagateLookup(trace,node)
      else:
        weight += applyPSP(trace,node,scaffold,shouldRestore,omegaDB,gradients)
        if isRequestNode(node): weight += evalRequests(trace,node,scaffold,shouldRestore,omegaDB,gradients)
    trace.incRegenCountAt(scaffold,node)
  weight += maybeRegenStaleAAA(trace, node, scaffold, shouldRestore, omegaDB, gradients)

  assert isinstance(weight, numbers.Number)
  return weight

def propagateLookup(trace, node):
  trace.setValueAt(node, trace.valueAt(node.sourceNode))

def maybeRegenStaleAAA(trace, node, scaffold, shouldRestore, omegaDB, gradients):
  # "[this] has to do with worries about crazy thing[s] that can
  # happen if aaa makers are shuffled around as first-class functions,
  # and the made SPs are similarly shuffled, including with stochastic
  # flow of such data, which may cause regeneration order to be hard
  # to predict, and the check is trying to avoid a stale AAA aux"
  # TODO: apparently nothing in the test suite actually hits this
  # case. can we come up with an example that does?
  weight = 0
  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode != node and scaffold.isAAA(value.makerNode):
    weight += regen(trace,value.makerNode,scaffold,shouldRestore,omegaDB,gradients)
  return weight

def evalFamily(trace,address,exp,env,scaffold,shouldRestore,omegaDB,gradients):
  if e.isVariable(exp):
    try:
      sourceNode = env.findSymbol(exp)
    except VentureError as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address), None, info[2]
    weight = regen(trace,sourceNode,scaffold,shouldRestore,omegaDB,gradients)
    return (weight,trace.createLookupNode(address,sourceNode))
  elif e.isSelfEvaluating(exp): return (0,trace.createConstantNode(address,exp))
  elif e.isQuotation(exp): return (0,trace.createConstantNode(address,e.textOfQuotation(exp)))
  else:
    weight = 0
    nodes = []
    for index, subexp in enumerate(exp):
      addr = address.extend(index)
      w, n = evalFamily(trace,addr,subexp,env,scaffold,shouldRestore,omegaDB,gradients)
      weight += w
      nodes.append(n)

    (requestNode,outputNode) = trace.createApplicationNodes(address,nodes[0],nodes[1:],env)
    try:
      weight += apply(trace,requestNode,outputNode,scaffold,shouldRestore,omegaDB,gradients)
    except VentureNestedRiplMethodError as err:
      # This is a hack to allow errors raised by inference SP actions
      # that are ripl actions to blame the address of the maker of the
      # action rather than the current address, which is the
      # application of that action (which is where the mistake is
      # detected).
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=err.addr, cause=err), None, info[2]
    except VentureException:
      raise # Avoid rewrapping with the below
    except Exception as err:
      import sys
      info = sys.exc_info()
      raise VentureException("evaluation", err.message, address=address, cause=err), None, info[2]
    assert isinstance(weight, numbers.Number)
    return weight,outputNode

def apply(trace,requestNode,outputNode,scaffold,shouldRestore,omegaDB,gradients):
  weight = applyPSP(trace,requestNode,scaffold,shouldRestore,omegaDB,gradients)
  weight += evalRequests(trace,requestNode,scaffold,shouldRestore,omegaDB,gradients)
  assert len(trace.esrParentsAt(outputNode)) == len(trace.valueAt(requestNode).esrs)
  weight += regenESRParents(trace,outputNode,scaffold,shouldRestore,omegaDB,gradients)
  weight += applyPSP(trace,outputNode,scaffold,shouldRestore,omegaDB,gradients)
  assert isinstance(weight, numbers.Number)
  return weight

def processMadeSP(trace,node,isAAA):
  spRecord = trace.valueAt(node)
  assert isinstance(spRecord,VentureSPRecord)
  trace.setMadeSPRecordAt(node,spRecord)
  if isAAA:
    trace.discardAAAMadeSPAuxAt(node)
  if spRecord.sp.hasAEKernel(): trace.registerAEKernel(node)
  trace.setValueAt(node,SPRef(node))

def applyPSP(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  weight = 0
  psp,args = trace.pspAt(node),trace.argsAt(node)
  assert isinstance(psp, PSP)

  if omegaDB.hasValueFor(node): oldValue = omegaDB.getValue(node)
  else: oldValue = None

  if scaffold.hasLKernel(node):
    k = scaffold.getLKernel(node)
    newValue = k.forwardSimulate(trace,oldValue,args) if not shouldRestore else oldValue
    weight += k.forwardWeight(trace,newValue,oldValue,args)
    assert isinstance(weight, numbers.Number)
    if isinstance(k,VariationalLKernel):
      gradients[node] = k.gradientOfLogDensity(newValue,args)
  else:
    # if we simulate from the prior, the weight is 0
    newValue = psp.simulate(args) if not shouldRestore else oldValue

  trace.setValueAt(node,newValue)
  psp.incorporate(newValue,args)

  if isinstance(newValue,VentureSPRecord): processMadeSP(trace,node,scaffold.isAAA(node))
  if psp.isRandom(): trace.registerRandomChoice(node)
  if isTagOutputPSP(psp):
    scope,block = [trace.valueAt(n) for n in node.operandNodes[0:2]]
    blockNode = node.operandNodes[2]
    trace.registerRandomChoiceInScope(scope,block,blockNode)
  assert isinstance(weight, numbers.Number)
  return weight

def evalRequests(trace,node,scaffold,shouldRestore,omegaDB,gradients):
  assert isRequestNode(node)
  weight = 0
  request = trace.valueAt(node)

  # first evaluate exposed simulation requests (ESRs)
  for esr in request.esrs:
    if not trace.containsSPFamilyAt(node,esr.id):
      if shouldRestore and omegaDB.hasESRParent(trace.spAt(node),esr.id):
        esrParent = omegaDB.getESRParent(trace.spAt(node),esr.id)
        weight += restore(trace,esrParent,scaffold,omegaDB,gradients)
      else:
        address = node.address.request(esr.addr)
        (w,esrParent) = evalFamily(trace,address,esr.exp,esr.env,scaffold,shouldRestore,omegaDB,gradients)
        weight += w
      if trace.containsSPFamilyAt(node,esr.id):
        # evalFamily already registered a family with this id for the
        # operator being applied here, which means a recursive call to
        # the operator issued a request for the same id.  Currently,
        # the only way for that it happen is for a recursive memmed
        # function to call itself with the same arguments.
        raise VentureException("evaluation", "Recursive mem argument loop detected.", address = node.address)
      trace.registerFamilyAt(node,esr.id,esrParent)

    esrParent = trace.spFamilyAt(node,esr.id)
    trace.addESREdge(esrParent,node.outputNode)

  # next evaluate latent simulation requests (LSRs)
  for lsr in request.lsrs:
    if omegaDB.hasLatentDB(trace.spAt(node)): latentDB = omegaDB.getLatentDB(trace.spAt(node))
    else: latentDB = None
    weight += trace.spAt(node).simulateLatents(trace.spauxAt(node),lsr,shouldRestore,latentDB)

  assert isinstance(weight, numbers.Number)
  return weight

def restore(trace,node,scaffold,omegaDB,gradients):
  if isConstantNode(node): return 0
  if isLookupNode(node):
    weight = regenParents(trace,node,scaffold,True,omegaDB,gradients)
    trace.reconnectLookup(node)
    trace.setValueAt(node,trace.valueAt(node.sourceNode))
    assert isinstance(weight, numbers.Number)
    return weight
  else: # node is output node
    assert isOutputNode(node)
    weight = restore(trace,node.operatorNode,scaffold,omegaDB,gradients)
    for operandNode in node.operandNodes: weight += restore(trace,operandNode,scaffold,omegaDB,gradients)
    weight += apply(trace,node.requestNode,node,scaffold,True,omegaDB,gradients)
    assert isinstance(weight, numbers.Number)
    return weight
