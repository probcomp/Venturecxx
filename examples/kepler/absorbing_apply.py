from venture.lite.exception import VentureValueError
from venture.lite.node import FixedValueArgs
from venture.lite.psp import NullRequestPSP, RandomPSP
from venture.lite.sp import SPType
from venture.lite.sp_help import typed_nr
import venture.lite.types as t

class AbsorbingApplyOutputPSP(RandomPSP):
  def _get_psp_and_args(self, args):
    operator = args.args.trace.groundValueAt(args.operandNodes[0])
    if not isinstance(operator.sp.requestPSP, NullRequestPSP):
      raise VentureValueError("Cannot absorb a requesting SP.")
    if not operator.sp.outputPSP.isRandom():
      raise VentureValueError("Cannot absorb a deterministic SP.")
    psp = operator.sp.outputPSP
    fargs = FixedValueArgs(
      args, args.operandValues()[1:],
      operandNodes=args.operandNodes[1:],
      spaux=operator.spAux)
    return psp, fargs

  def simulate(self, args):
    psp, fargs = self._get_psp_and_args(args)
    return psp.simulate(fargs)

  def gradientOfSimulate(self, args, value, direction):
    psp, fargs = self._get_psp_and_args(args)
    dargs = psp.gradientOfSimulate(fargs, value, direction)
    return [0] + dargs

  def logDensity(self, value, args):
    psp, fargs = self._get_psp_and_args(args)
    return psp.logDensity(value, fargs)

  def gradientOfLogDensity(self, value, args):
    psp, fargs = self._get_psp_and_args(args)
    dvalue, dargs = psp.gradientOfLogDensity(value, fargs)
    return dvalue, [0] + dargs

  def logDensityBound(self, value, args):
    if args.operandValues()[0] is None:
      raise Exception("Cannot rejection sample application of unknown procedure")
    psp, fargs = self._get_psp_and_args(args)
    return psp.logDensityBound(value, fargs)

  def incorporate(self, value, args):
    psp, fargs = self._get_psp_and_args(args)
    psp.incorporate(value, fargs)

  def unincorporate(self, value, args):
    psp, fargs = self._get_psp_and_args(args)
    psp.unincorporate(value, fargs)

  def enumerateValues(self, args):
    psp, fargs = self._get_psp_and_args(args)
    return psp.enumerateValues(fargs)

def __venture_start__(ripl, *args):
  ripl.bind_foreign_sp("absorbing_apply", typed_nr(
    AbsorbingApplyOutputPSP(),
    [SPType([t.AnyType("<args>")], t.AnyType("<result>"), variadic=True)],
    t.AnyType("<result>")))
