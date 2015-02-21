from value import VentureValue, registerVentureType, VentureType
from psp import DeterministicPSP, NullRequestPSP, TypedPSP
from sp import SP, SPType
import venture.value.dicts as v

"""This doesn't subclass VentureSPRecord, as if it did, then
the trace would turn it into an SPRef. While this would make it
a first-class function in Venture, it would prevent other SPs
(like a GP) from using it as a function without requests."""
class VentureFunction(VentureValue):
  def __init__(self, f, args_types=None, return_type=None, sp_type=None, **kwargs):
    if sp_type is not None:
      args_types = sp_type.args_types
      return_type = sp_type.return_type
    else:
      sp_type = SPType(args_types, return_type)

    self.f = f
    self.sp_type = sp_type
    self.stuff = kwargs
  
  @staticmethod
  def fromStackDict(thing):
    return VentureFunction(thing['value'], **thing)
  
  def asStackDict(self, _trace=None):
    val = v.val("function", self.f)
    val["sp_type"] = self.sp_type
    val.update(self.stuff)
    return val
  
  def __call__(self, *args):
    return self.f(*args)

registerVentureType(VentureFunction, "function")

class ApplyFunctionOutputPSP(DeterministicPSP):
  def simulate(self,args):
    function = args.operandValues[0]
    arguments = args.operandValues[1:]
    
    sp_type = function.sp_type
    unwrapped_args = sp_type.unwrap_arg_list(arguments)
    #print sp_type.name(), unwrapped_args
    
    returned = function.f(*unwrapped_args)
    wrapped_return = sp_type.wrap_return(returned)
    
    return wrapped_return
  
  def description(self,_name=None):
    return "Apply a VentureFunction to arguments."

# TODO Add type signature. Look at signature of apply?
applyFunctionSP = SP(NullRequestPSP(), ApplyFunctionOutputPSP())

