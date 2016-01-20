# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

from venture.lite.psp import DeterministicPSP
from venture.lite.psp import TypedPSP
from venture.lite.sp_help import typed_nr
from venture.lite.sp_registry import registerBuiltinSP
from venture.lite.utils import override
import venture.lite.types as t

class TagOutputPSP(DeterministicPSP):
  @override(DeterministicPSP)
  def simulate(self,args): return args.operandValues()[2]
  @override(DeterministicPSP)
  def gradientOfSimulate(self, _args, _value, direction): return [0, 0, direction]
  @override(DeterministicPSP)
  def canAbsorb(self, _trace, appNode, parentNode): return parentNode != appNode.operandNodes[2]

  @override(DeterministicPSP)
  def description(self,name):
    return "%s returns its third argument unchanged at runtime, but tags the subexpression creating the object as being within the given scope and block." % name

def isTagOutputPSP(thing):
  return isinstance(thing, TagOutputPSP) or \
    (isinstance(thing, TypedPSP) and isTagOutputPSP(thing.psp))

registerBuiltinSP("tag", typed_nr(TagOutputPSP(),
                                  # These are type-restricted in Venture, but the actual PSP doesn't care.
                                  [t.AnyType("<scope>"), t.AnyType("<block>"), t.AnyType()],
                                  t.AnyType()))

class TagExcludeOutputPSP(DeterministicPSP):
  @override(DeterministicPSP)
  def simulate(self,args): return args.operandValues()[1]
  @override(DeterministicPSP)
  def gradientOfSimulate(self, _args, _value, direction): return [0, direction]
  @override(DeterministicPSP)
  def canAbsorb(self, _trace, appNode, parentNode): return parentNode != appNode.operandNodes[1]

  @override(DeterministicPSP)
  def description(self,name):
    return "%s returns its second argument unchanged at runtime, but tags the subexpression creating the object as being outside the given scope." % name

def isTagExcludeOutputPSP(thing):
  return isinstance(thing, TagExcludeOutputPSP) or \
    (isinstance(thing, TypedPSP) and isTagExcludeOutputPSP(thing.psp))

registerBuiltinSP("tag_exclude", typed_nr(TagExcludeOutputPSP(),
                                          # These are type-restricted in Venture, but the actual PSP doesn't care.
                                          [t.AnyType("<scope>"), t.AnyType()],
                                          t.AnyType()))
