from psp import PSP

class PlusOutputPSP(PSP):
  def simulate(self,args): return sum(args.operandValues)

class MinusOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0] - args.operandValues[1]

class TimesOutputPSP(PSP):
  def simulate(self,args): return reduce(lambda x,y: x * y,args.operandValues)

class DivideOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0] / args.operandValues[1]

class EqualOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0] == args.operandValues[1]

class LessThanOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0] <  args.operandValues[1]

class GreaterThanOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0] > args.operandValues[1]

# Only makes sense with VentureAtom/VentureNumber distinction
class RealOutputPSP(PSP):
  def simulate(self,args): return args.operandValues[0]

