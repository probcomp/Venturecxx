# Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

from node import LookupNode, RequestNode, OutputNode
from value import SPRef
from omegadb import OmegaDB
from detach import unapplyPSP
from regen import applyPSP

class Scaffold(object):
  def __init__(self,setsOfPNodes=None,regenCounts=None,absorbing=None,aaa=None,border=None,lkernels=None,brush=None):
    self.setsOfPNodes = setsOfPNodes if setsOfPNodes else [] # [Set Node]
    self.regenCounts = regenCounts if regenCounts else {} # {Node:Int}
    self.absorbing = absorbing if absorbing else set() # Set Node
    self.aaa = aaa if aaa else set() # Set Node
    self.border = border if border else [] # [[Node]]
    self.lkernels = lkernels if lkernels else {} # {Node:LKernel}
    self.brush = brush if brush else set() # Set Node

  def getPrincipalNodes(self):
    # Return a list so that repeated traversals have the same order
    return [n for n in set.union(*self.setsOfPNodes)]
  def getRegenCount(self,node): return self.regenCounts[node]
  def incrementRegenCount(self,node): self.regenCounts[node] += 1
  def decrementRegenCount(self,node): self.regenCounts[node] -= 1
  def isResampling(self,node): return node in self.regenCounts
  def isAbsorbing(self,node): return node in self.absorbing
  def isAAA(self,node): return node in self.aaa
  def hasLKernel(self,node): return node in self.lkernels
  def getLKernel(self,node): return self.lkernels[node]
  def getPNode(self):
    assert len(self.setsOfPNodes) == 1
    pnodes = []
    for pnode in self.setsOfPNodes[0]: pnodes.append(pnode)
    assert len(pnodes) == 1
    return pnodes[0]
  def isBrush(self, node): return node in self.brush

  def show(self):
    print "---Scaffold---"
    print "# pnodes: " + str(len(self.getPrincipalNodes()))
    print "# absorbing nodes: " + str(len(self.absorbing))
    print "# aaa nodes: " + str(len(self.aaa))
    print "border lengths: " + str([len(segment) for segment in self.border])
    print "# lkernels: " + str(len(self.lkernels))

  def showMore(self):
    print "---Scaffold---"
    print "pnodes: " + str(self.getPrincipalNodes())
    print "absorbing nodes: " + str(self.absorbing)
    print "aaa nodes: " + str(self.aaa)
    print "borders: " + str(self.border)
    print "lkernels: " + str(self.lkernels)

# Calling subsampled_mh may create broken deterministic
# relationships in the trace.  For example, consider updating mu in the
# program:
#
# [assume mu (normal 0 1)]
# [assume x (lambda () (normal mu 1))]
# [observe (x) 0.1]
# [observe (x) 0.2]
# ...
# N observations
# ...
#
# If the subsampled scaffold only included the first n observations, the
# lookup nodes for mu in the remaining N-n observations will have a
# stale value.  At a second call to infer, these inconsistencies may cause
# a problem.
#
# updateValuesAtScaffold updates all the nodes in a newly constructed
# scaffold by calling updateValueAtNode for each node. The main idea is:
# - Assume all the random output nodes have the latest values and the
#   problem is in the nodes with deterministic dependence on their
#   parents.
# - For every node that cannot absorb, update the value of all its
#   parents, and then unapplyPSP and applyPSP.
#
# Assumptions/Limitations:
# Currently we assume the stale values do not change the structure of
# the trace (the existence of ESRs) and the value of the request node is
# always up to date.  Also, we assume the values of brush/border nodes
# and their parents are up to date.  As a result, we only update the
# application and lookup nodes in the DRG.
def updateValuesAtScaffold(trace,scaffold,updatedNodes):
  for node in scaffold.regenCounts:
    updateValueAtNode(trace, scaffold, node, updatedNodes)

def updateValueAtNode(trace, scaffold, node, updatedNodes):
  # Strong assumption! Only consider resampling nodes in the scaffold.
  if node not in updatedNodes and scaffold.isResampling(node):
    if isinstance(node, LookupNode):
      updateValueAtNode(trace, scaffold, node.sourceNode, updatedNodes)
      trace.setValueAt(node, trace.valueAt(node.sourceNode))
    elif isinstance(node, OutputNode):
      # Assume SPRef and AAA nodes are always updated.
      psp = trace.pspAt(node)
      if not isinstance(trace.valueAt(node), SPRef) and not psp.childrenCanAAA():
        canAbsorb = True
        for parent in trace.parentsAt(node):
          if not psp.canAbsorb(trace, node, parent):
            updateValueAtNode(trace, scaffold, parent, updatedNodes)
            canAbsorb = False
        if not canAbsorb:
          update(trace, node)
    updatedNodes.add(node)

def update(trace, node):
  scaffold = Scaffold()
  omegaDB = OmegaDB()
  unapplyPSP(trace, node, scaffold, omegaDB)
  applyPSP(trace,node,scaffold,False,omegaDB,{})


def constructScaffold(trace, setsOfPNodes, useDeltaKernels=False, deltaKernelArgs=None, hardBorder=None, updateValues=False):
  if hardBorder is None:
    hardBorder = []
  assert len(hardBorder) <= 1

  cDRG,cAbsorbing,cAAA = set(),set(),set()
  indexAssignments = {}
  assert isinstance(setsOfPNodes,list)
  for i in range(len(setsOfPNodes)):
    assert isinstance(setsOfPNodes[i],set)
    extendCandidateScaffold(trace,setsOfPNodes[i],cDRG,cAbsorbing,cAAA,indexAssignments,i,hardBorder)

  brush = findBrush(trace,cDRG)
  drg,absorbing,aaa = removeBrush(cDRG,cAbsorbing,cAAA,brush)
  border = findBorder(trace,drg,absorbing,aaa)
  regenCounts = computeRegenCounts(trace,drg,absorbing,aaa,border,brush,hardBorder)
  for node in hardBorder: assert node in border
  lkernels = loadKernels(trace,drg,aaa,useDeltaKernels,deltaKernelArgs)
  borderSequence = assignBorderSequnce(border,indexAssignments,len(setsOfPNodes))
  scaffold = Scaffold(setsOfPNodes,regenCounts,absorbing,aaa,borderSequence,lkernels,brush)

  if updateValues:
    updateValuesAtScaffold(trace,scaffold,set())

  return scaffold

def addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i,hardBorder):
  if node not in hardBorder:
    if node not in drg or node not in indexAssignments or indexAssignments[node] is not i or node in absorbing or node in aaa:
      q.extend([(n,False,node) for n in trace.childrenAt(node)])
  if node in absorbing: absorbing.remove(node)
  if node in aaa: aaa.remove(node)
  drg.add(node)
  indexAssignments[node] = i

def addAbsorbingNode(drg,absorbing,aaa,node,indexAssignments,i):
  assert not node in drg
  assert not node in aaa
  absorbing.add(node)
  indexAssignments[node] = i

def addAAANode(drg,aaa,absorbing,node,indexAssignments,i):
  if node in absorbing: absorbing.remove(node)
  drg.add(node)
  aaa.add(node)
  indexAssignments[node] = i


def extendCandidateScaffold(trace,pnodes,drg,absorbing,aaa,indexAssignments,i,hardBorder):
  q = [(pnode,True,None) for pnode in pnodes]

  while q:
    node,isPrincipal,parentNode = q.pop()
    if node in drg and not node in aaa:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i,hardBorder)
    elif isinstance(node,LookupNode) or node.operatorNode in drg:
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i,hardBorder)
    # TODO temporary: once we put all uncollapsed AAA procs into AEKernels, this line won't be necessary
    elif node in aaa:
      addAAANode(drg,aaa,absorbing,node,indexAssignments,i)      
    elif (not isPrincipal) and trace.pspAt(node).canAbsorb(trace,node,parentNode):
      addAbsorbingNode(drg,absorbing,aaa,node,indexAssignments,i)
    elif trace.pspAt(node).childrenCanAAA(): 
      addAAANode(drg,aaa,absorbing,node,indexAssignments,i)
    else: 
      addResamplingNode(trace,drg,absorbing,aaa,q,node,indexAssignments,i,hardBorder)

def findBrush(trace,cDRG):
  disableCounts = {}
  disabledRequests = set()
  brush = set()
  for node in cDRG:
    if isinstance(node,RequestNode):
      disableRequests(trace,node,disableCounts,disabledRequests,brush)
  return brush

def disableRequests(trace,node,disableCounts,disabledRequests,brush):
  if node in disabledRequests: return
  disabledRequests.add(node)
  for esrParent in trace.esrParentsAt(node.outputNode):
    if not esrParent in disableCounts: disableCounts[esrParent] = 0
    disableCounts[esrParent] += 1
    if disableCounts[esrParent] == esrParent.numRequests:
      disableFamily(trace,esrParent,disableCounts,disabledRequests,brush)

def disableFamily(trace,node,disableCounts,disabledRequests,brush):
  if node in brush: return
  brush.add(node)
  if isinstance(node,OutputNode):
    brush.add(node.requestNode)
    disableRequests(trace,node.requestNode,disableCounts,disabledRequests,brush)
    disableFamily(trace,node.operatorNode,disableCounts,disabledRequests,brush)
    for operandNode in node.operandNodes: 
      disableFamily(trace,operandNode,disableCounts,disabledRequests,brush)

def removeBrush(cDRG,cAbsorbing,cAAA,brush):
  drg = cDRG - brush
  absorbing = cAbsorbing - brush
  aaa = cAAA - brush
  assert aaa.issubset(drg)
  assert not drg.intersection(absorbing)
  return drg,absorbing,aaa

def hasChildInAorD(trace,drg,absorbing,node):
  kids = trace.childrenAt(node)
  return kids.intersection(drg) or kids.intersection(absorbing)

def findBorder(trace,drg,absorbing,aaa):
  border = absorbing.union(aaa)
  for node in drg - aaa:
    if not hasChildInAorD(trace,drg,absorbing,node): border.add(node)
  return border

def maybeIncrementAAARegenCount(trace,regenCounts,aaa,node):
  value = trace.valueAt(node)
  if isinstance(value,SPRef) and value.makerNode in aaa: 
    regenCounts[value.makerNode] += 1

def computeRegenCounts(trace,drg,absorbing,aaa,border,brush,hardBorder):
  regenCounts = {}
  for node in drg:
    if node in aaa:
      regenCounts[node] = 1 # will be added to shortly
    elif node in hardBorder:
      # hardBorder nodes will regenerate despite the number of children.
      regenCounts[node] = 1
    elif node in border:
      regenCounts[node] = len(trace.childrenAt(node)) + 1
    else:
      regenCounts[node] = len(trace.childrenAt(node))

  if aaa:
    for node in drg.union(absorbing):
      for parent in trace.parentsAt(node):
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,parent)

    for node in brush:
      if isinstance(node,OutputNode):
        for esrParent in trace.esrParentsAt(node):
          maybeIncrementAAARegenCount(trace,regenCounts,aaa,esrParent)
      elif isinstance(node,LookupNode):
        maybeIncrementAAARegenCount(trace,regenCounts,aaa,node.sourceNode)

  return regenCounts

def loadKernels(trace,drg,aaa,useDeltaKernels,deltaKernelArgs):
  lkernels = { node : trace.pspAt(node).getAAALKernel() for node in aaa}
  if useDeltaKernels:
    for node in drg - aaa:
      if not isinstance(node,OutputNode): continue
      if node.operatorNode in drg: continue
      for o in node.operandNodes:
        if o in drg: continue
      if trace.pspAt(node).hasDeltaKernel(): lkernels[node] = trace.pspAt(node).getDeltaKernel(deltaKernelArgs)
  return lkernels

def assignBorderSequnce(border,indexAssignments,numIndices):
  borderSequence = [[] for _ in range(numIndices)]
  for node in border:
    borderSequence[indexAssignments[node]].append(node)
  return borderSequence

