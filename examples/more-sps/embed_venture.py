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
from venture.lite.request import Request
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord
from venture.lite.sp_help import typed_nr
from venture.lite.value import VentureValue, VentureForeignBlob
import venture.lite.types as t

from venture.shortcuts import make_lite_church_prime_ripl

class MakeEmbeddedVentureOutputPSP(DeterministicPSP):
  def simulate(self, args):
    [prefix_program, infer_program] = args.operandValues()
    return VentureSPRecord(EmbeddedVentureSP(prefix_program, infer_program))

class EmbeddedVentureSPAux(SPAux):
  def __init__(self, ripl):
    self.ripl = ripl

  def asVentureValue(self):
    return VentureForeignBlob(self.ripl)

class EmbeddedVentureSP(SP):
  def __init__(self, prefix_program, infer_program):
    req = TypedPSP(EmbeddedVentureRequestPSP(), SPType([t.ExpressionType()], t.RequestType()))
    output = TypedPSP(EmbeddedVentureOutputPSP(), SPType([t.ExpressionType()], t.AnyType()))
    super(EmbeddedVentureSP, self).__init__(req, output)
    self.prefix_program = prefix_program
    self.infer_program = infer_program

  def constructSPAux(self):
    ripl = make_lite_church_prime_ripl()
    ripl.evaluate(self.prefix_program)
    return EmbeddedVentureSPAux(ripl)

  def simulateLatents(self, args, lsr, shouldRestore, latentDB):
    (label, exp) = lsr
    spaux = args.spaux()
    spaux.ripl.predict(exp, label=label)
    return 0

  def detachLatents(self, args, lsr, latentDB):
    (label, _) = lsr
    spaux = args.spaux()
    spaux.ripl.forget(label)
    return 0

  def hasAEKernel(self): return True

  def AEInfer(self, spaux):
    # TODO can we clamp the output variables so we don't change their values from under them?
    spaux.ripl.evaluate(self.infer_program)

class EmbeddedVentureRequestPSP(DeterministicPSP):
  def simulate(self, args):
    [exp] = args.operandValues()
    label = 'req_%d' % hash(args.node)
    return Request([], [(label, exp)])

class EmbeddedVentureOutputPSP(DeterministicPSP):
  def simulate(self, args):
    spaux = args.spaux()
    label = 'req_%d' % hash(args.node.requestNode)
    return VentureValue.fromStackDict(spaux.ripl.report(label, type=True))

def __venture_start__(ripl, *args):
  ripl.bind_foreign_sp("make_venture", typed_nr(
    MakeEmbeddedVentureOutputPSP(),
    [t.ExpressionType(), t.ExpressionType()],
    SPType([t.ExpressionType()], t.AnyType())))
