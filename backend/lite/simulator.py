import random
import math
import scipy
import scipy.special
import numpy.random as npr
from utils import simulateCategorical, logDensityCategorical, simulateDirichlet, logDensityDirichlet
from psp import PSP, NullRequestPSP, RandomPSP
from sp import VentureSP,SPAux
from lkernel import LKernel
from nose.tools import assert_equal,assert_greater_equal
import copy
import win32com.client
from Wormhole import Wormhole
import uuid
import pdb 

class SimulatorSPAux(SPAux):
  def __init__(self, path_to_folder, seed, port, h = None, old_parid = 0):
    self.seed = str(seed) #"201403070"
    self.path_to_folder = path_to_folder
    self.port = port
    print port
    if h is None:
      print h
      print port
      print path_to_folder
      #self.h = win32com.client.DispatchEx('matlab.application')
      self.h = Wormhole(int(port))
      #make temp state a string in self.state_file
      self.h.execute("seed ="+self.seed) #need to change this for a new run (FIXIT later)
      self.h.execute("rng(seed)")
      self.h.execute(r"cd C:\Shell_runs\Shell_reformulated_"+str(int(port))+"\Matlab_code") #C:\Shell_runs\Shell_reformulated_5001\Matlab_code
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
  def __init__(self,requestPSP,outputPSP, path_to_folder, seed, port):
    super(SimulatorSP,self).__init__(requestPSP,outputPSP)
    self.path_to_folder = path_to_folder 
    self.seed = seed
    self.port = port
  def constructSPAux(self): return SimulatorSPAux(self.path_to_folder, self.seed, self.port)

class MakeSimulatorOutputPSP(PSP):
  def simulate(self,args):
    path_to_folder = args.operandValues[0]
    seed = args.operandValues[1]
    port = args.operandValues[2]
    return SimulatorSP(NullRequestPSP(),SimulatorOutputPSP(),path_to_folder, seed, port)

  #def description(self,name): #FIXME ARDAVAN
   # raise Exception ("not implemented") 
 



class SimulatorOutputPSP(PSP):
  def isRandom(self): return True
  def simulate(self,args):
    spaux = args.spaux
    seed = spaux.seed
    methodname = args.operandValues[0]
    print "----",methodname, spaux.old_parid, spaux.new_parid
    if methodname == "simulate":
      # args = ("simulate",params::VentureVector{VentureNumber}
      params = args.operandValues[1]
      print params
      iter_num = args.operandValues[2]
      f1=open('./'+seed, 'a')
      f1.write(str(iter_num) + ' ')
      print 'iter_num', str(iter_num)
      expression = "simulate(" + spaux.state_file_address + ",'" + str(spaux.old_parid) + "','" + str(spaux.new_parid) + "'," + str(params) +","+ str(iter_num)+")";
      f1=open('./testfile', 'a')
      f1.write(expression + '\n')
      spaux.h.execute(expression)
      return True
        
    elif methodname == "initialize":
      # args = ("initialize")
      expression = "initialize(" + spaux.state_file_address + ")";
      print expression
      f1=open('./testfile', 'a')
      f1.write(expression + '\n')
      spaux.h.execute(expression) 
      return True;

    elif methodname == "emit":
      expression = "emit(" + spaux.state_file_address + ",'" + str(spaux.new_parid) +"')";
      f1=open('./testfile', 'a')
      f1.write(expression + '\n')
      spaux.h.execute(expression)
      return True;
      
    elif methodname == "distance":
      expression = "[real_error, error, total_size] = distance(" + spaux.state_file_address + ",'" + str(spaux.new_parid) +"')";
      f1=open('./testfile', 'a')
      f1.write(expression + '\n')
      computed_distance = spaux.h.execute(expression)
      #computed_distance = computed_distance.replace("ans =", "")
      computed_distance = spaux.h.get("real_error")
      print computed_distance
      computed_distance = -1 * float(computed_distance)
      error = -1 * spaux.h.get("error") 
      total_size = spaux.h.get("total_size")
      f1=open('./'+seed, 'a')
      f1.write(' '+ str(computed_distance) + ' ' + str(error[0][0]) + ' ' + str(total_size[0][0]) + '\n')
      print computed_distance
      return computed_distance;

    else:
      raise Exception ('unknown method name')
            
      

      
      #make distance return sth
      #change the name of the functions to simulate, emit,...
      #make sure old_parid and new_parid are passed from Venture (check if we are doing the same thing as before)
      #fill out the rest of submethods 
      
      
      
