from abc import ABCMeta, abstractmethod
from request import Request


class PSP():
  __metaclass__ = ABCMeta

  @abstractmethod
  def simulate(self,args): pass
  def logDensity(self,value,args): return 0
  def incorporate(self,value,args): pass
  def unincorporate(self,value,args): pass
  def enumerate(self,args): return []
  def isRandom(self): return False
  def canAbsorb(self): return False
  def makesHSRs(self): return False
  def canEnumerate(self): return False
  def hasVariationalKernel(self): return False
  def hasSimulationKernel(self): return False
  def hasDeltaKernel(self): return False

class NullRequestPSP(PSP):
  def simulate(self,args): return Request()
  def canAbsorb(self): return True

class ESRRefOutputPSP(PSP):
  def simulate(self,args):
    assert len(args.esrParents) ==  1
    return args.esrParents[0]
