import scipy.special
import scipy.stats
from numerical import *
from utilities import structToArrays
import numpy as np
import random

class NormalOutputPSP(PSP):
  def normalSample(mu,sigma): return scipy.stats.norm.rvs(mu,sigma)
  def normalLogDensity(x,mu,sigma): return scipy.stats.norm.logpdf(x,mu,sigma)
    
  def simulate(self,args):
    (mu,sigma) = args.operandValues[0:2]
    return normalSample(mu,sigma)

  def logDensity(self,x,args):
    (mu,sigma) = args.operandValues[0:2]
    return normalLogDensity(x,mu,sigma)

  def canAbsorb(self): return True
      
