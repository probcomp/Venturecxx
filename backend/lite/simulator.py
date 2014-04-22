import random
import math
import scipy
import scipy.special
import numpy.random as npr
from utils import simulateCategorical, logDensityCategorical, simulateDirichlet, logDensityDirichlet
from psp import PSP, NullRequestPSP, DeterministicPSP
from sp import VentureSP,SPAux
from value import VentureBool, VentureNumber, VentureSymbol
from lkernel import LKernel
from nose.tools import assert_equal,assert_greater_equal
import copy
import win32com.client
from Wormhole import Wormhole
import uuid
import pdb 

"""
class SimulatorSPAux(SPAux):
  def __init__(self, path_to_folder, seed, port, h = None, old_parid = 0):
    self.seed = seed #"201403070"
    self.path_to_folder = path_to_folder
    self.port = port
    print port
    if h is None:
      print h
      print port
      print path_to_folder
      #self.h = win32com.client.DispatchEx('matlab.application')
      self.h = Wormhole(self.port)
      #make temp state a string in self.state_file
      self.h.execute("seed ="+str(self.seed)) #need to change this for a new run (FIXIT later)
      self.h.execute("rng(seed)")
      self.h.execute(r"cd C:\Shell_runs\Shell_reformulated_"+str(self.port)+"\Matlab_code") #C:\Shell_runs\Shell_reformulated_5001\Matlab_code
      self.h.execute("save('temp_state')")	 
      #pdb.set_trace()
    else:
      self.h = h
    self.state_file_address = "'temp_state'"
    print self.state_file_address
    self.old_parid = old_parid
    self.new_parid = uuid.uuid4()
      
  def copy(self): 
    return SimulatorSPAux(None, self.seed, self.port, self.h, self.new_parid)
      


class SimulatorSP(VentureSP):
  def __init__(self,requestPSP,outputPSP, seed, port):
    super(SimulatorSP,self).__init__(requestPSP,outputPSP)
    self.seed = seed
    self.port = port
  #def constructSPAux(self): return SimulatorSPAux(self.path_to_folder, self.seed, self.port)
"""

class MakeSimulatorOutputPSP(DeterministicPSP):
  def simulate(self,args):
    #path_to_folder = args.operandValues[0].getSymbol()
    seed = str(int(args.operandValues[0].getNumber()))
    port = int(args.operandValues[1].getNumber())
    
    matlab = Wormhole(port)
    matlab.execute("seed ="+seed) #need to change this for a new run (FIXIT later)
    matlab.execute("rng(seed)")
    matlab.execute(r"cd C:\Shell_cleaned_05182014\Shell_reformulated_"+str(port)+"\Matlab_code") #C:\Shell_runs\Shell_reformulated_5001\Matlab_code
    
    return VentureSP(NullRequestPSP(),SimulatorOutputPSP(seed, port, matlab))

  #def description(self,name): #FIXME ARDAVAN
   # raise Exception ("not implemented") 
 



class SimulatorOutputPSP(DeterministicPSP):
  def __init__(self, seed, port, matlab):
    self.seed = seed
    self.port = port
    self.matlab = matlab

  def simulate(self,args):
    #spaux = args.spaux
    #seed = spaux.seed
    methodname = args.operandValues[0].getSymbol()
    print "----",methodname
    if methodname == "simulate":
      # args = ("simulate",params::VentureVector{VentureNumber}      
      old_file_id = int(args.operandValues[1].getNumber())
      params = [v.getNumber() for v in args.operandValues[2].getArray()]
      print old_file_id, params
      
      expression = "[return_id] = simulate('" + self.seed + "','" + str(old_file_id) + "'," + str(params) + ");"
      f1=open('./testfile', 'a')
      f1.write(expression + '\n')
      self.matlab.execute(expression)
      return VentureNumber(self.matlab.get("return_id")[0][0])
    
    elif methodname == "initialize":
      # args = ("initialize")
      expression = "[return_id] = initialize('" + self.seed + "');"
      print expression
      f1=open('./testfile', 'a')
      f1.write(expression + '\n')
      self.matlab.execute(expression)
      return_id = self.matlab.get("return_id")[0][0]
      #import pdb; pdb.set_trace()
      return VentureNumber(return_id)

    elif methodname == "emit":
      file_id = int(args.operandValues[1].getNumber())
      expression = "[return_id] = emit('" + self.seed + "','" + str(file_id) +"');"
      f1=open('./testfile', 'a')
      f1.write(expression + '\n')
      self.matlab.execute(expression)
      return VentureNumber(self.matlab.get("return_id")[0][0])
      
    elif methodname == "distance":
      obs_file_id = int(args.operandValues[1].getNumber())
      expression = "[real_error, error, total_size, new_file_id] = distance('" + self.seed + "','" + str(obs_file_id) + "');"
      f1=open('./testfile', 'a')
      f1.write(expression + '\n')
      self.matlab.execute(expression)
      computed_distance = self.matlab.get("real_error")[0][0]
      print computed_distance
      computed_distance = -1 * float(computed_distance)
      error = -1 * self.matlab.get("error") 
      total_size = self.matlab.get("total_size")
      f1=open('./'+self.seed, 'a')
      f1.write(' '+ str(computed_distance) + ' ' + str(error[0][0]) + ' ' + str(total_size[0][0]) + '\n')
      print computed_distance
      return VentureNumber(computed_distance)

    else:
      raise Exception ('unknown method name')
            
      

      
      #make distance return sth
      #change the name of the functions to simulate, emit,...
      #make sure old_parid and new_parid are passed from Venture (check if we are doing the same thing as before)
      #fill out the rest of submethods 
      
      
      
