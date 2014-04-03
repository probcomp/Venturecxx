from psp import DeterministicPSP
import value as v

### Dicts
class DictOutputPSP(DeterministicPSP):
  def simulate(self,args):
    keys = args.operandValues[0].asPythonList()
    vals = args.operandValues[1].asPythonList()
    return v.VentureDict(dict(zip(keys, vals)))
  def description(self,name):
    return "%s :: <SP <list k> <list v> -> <dictionary k v>>\n  Returns the dictionary mapping the given keys to their respective given values.  It is an error if the given lists are not the same length." % name

