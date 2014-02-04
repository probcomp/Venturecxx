from abc import ABCMeta, abstractmethod
from lkernel import DefaultAAALKernel,DefaultVariationalLKernel
from request import Request


class PSP(object):
  __metaclass__ = ABCMeta

  @abstractmethod
  def simulate(self,args): pass
  def logDensity(self,value,args): return 0
  def incorporate(self,value,args): pass
  def unincorporate(self,value,args): pass
  def enumerate(self,args): return []
  def isRandom(self): return False
  def canAbsorb(self,parentNode): return False

  def childrenCanAAA(self): return False
  def getAAALKernel(self): return DefaultAAALKernel(self)

  def makesHSRs(self): return False
  def canEnumerate(self): return False

  def hasVariationalLKernel(self): return False
  def getVariationalLKernel(self,trace,node): return DefaultVariationalLKernel(trace,self,node)

  def hasSimulationKernel(self): return False
  def hasDeltaKernel(self): return False

  def description(self,name): return None

class NullRequestPSP(PSP):
  def simulate(self,args): return Request()
  def canAbsorb(self,parentNode): return True

class ESRRefOutputPSP(PSP):
  def simulate(self,args):
    assert len(args.esrNodes) ==  1
    return args.esrValues[0]

class RandomPSP(PSP):
  def isRandom(self): return True
  def canAbsorb(self,parentNode): return True
