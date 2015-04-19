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

class OmegaDB(object):
  def __init__(self):
    self.latentDBs = {} # not sure if keys are nodes or sps
    self.values = {} # node => value
    self.spFamilyDBs = {} # makerNode,id => root

    # The partial derivative of the weight returned by the detach that
    # made this DB with respect to the value of this node, at the
    # value stored for this node in self.values.  Only meaningful for
    # nodes with continuous values.
    self.partials = {} # node => cotangent(value)

  def hasValueFor(self,node): return node in self.values
  def getValue(self,node): return self.values[node]

  def extractValue(self,node,value):
    assert not node in self.values
    self.values[node] = value

  def hasLatentDB(self,sp): return sp in self.latentDBs

  def registerLatentDB(self,sp,latentDB):
    assert not sp in self.latentDBs
    self.latentDBs[sp] = latentDB

  def getLatentDB(self,sp): return self.latentDBs[sp]

  def hasESRParent(self,sp,id): return (sp,id) in self.spFamilyDBs
  def getESRParent(self,sp,id): return self.spFamilyDBs[(sp,id)]
  def registerSPFamily(self,sp,id,esrParent):
    assert not (sp,id) in self.spFamilyDBs
    self.spFamilyDBs[(sp,id)] = esrParent

  def addPartials(self, nodes, partials):
    assert len(nodes) == len(partials)
    for (n, p) in zip(nodes, partials):
      self.addPartial(n, p)

  def addPartial(self, node, partial):
    if node not in self.partials:
      # TODO Get the correct zero for structured partials for
      # e.g. nodes with multi-dimensional outputs.
      self.partials[node] = 0
    self.partials[node] += partial

  def getPartial(self, node):
    if node not in self.partials:
      self.partials[node] = 0
    return self.partials[node]
