import numpy as np
import matplotlib.pyplot as plt
import venture.lite.types as t
import venture.lite.value as v
from venture.lite.sp_help import deterministic_typed
from venture.lite.sp import SP
from venture.lite.sp import SPAux
from venture.lite.sp import SPType
from venture.lite.sp import VentureSPRecord
from venture.lite.psp import DeterministicMakerAAAPSP
from venture.lite.psp import TypedPSP

from venture.lite.psp import NullRequestPSP


from venture.lite.psp import RandomPSP
from venture.lite.sp_help import typed_nr
import numpy as np

from pgmpy.models import BayesianModel

import sys
sys.path.insert(0, '/scratch/ulli/Venturecxx/examples/causal-inference')

from precomputed_cmi import precomputed_CMIs

def dag_to_dot_notation(dag):
    output_str = ""
    for i in range(len(dag)): 
        for j in range(len(dag)):
            if dag[i][j]:
                output_str+="(%d)-->(%d), " % (i,j,)
    return output_str


def get_independencies(dag):
    # convert to pgmpy representation
    nodes_pgmpy = ["node_%d" % (i,) for i in range(len(dag))]
    edges_pgmpy = []
    for i in range(len(dag)):
        for j in range(len(dag)):
            if dag[i][j]:
                edges_pgmpy.append(("node_%d" % (i,), "node_%d" % (j,)))
    b_net_model = BayesianModel()
    b_net_model.add_nodes_from(nodes_pgmpy) 
    b_net_model.add_edges_from(edges_pgmpy) 
    pgmpy_independencies_object = b_net_model.get_independencies()
    return pgmpy_independencies_object.independencies

class PopulationSPAux(SPAux):
  def __init__(self):
    self.field = {} 

  def copy(self):
    aux = PopulationSPAux()
    aux.field = self.field
    return aux




class PopulationSP(SP):
  def constructSPAux(self):
    return PopulationSPAux()

  def show(self,spaux):
    return spaux.field



class BDBPopulationOutputPSP(RandomPSP):
  def __init__(self, population_name):
    self.population_name = population_name

  def incorporate(self, value, args):
    spaux = args.spaux()
    spaux.field = value

  def unincorporate(self, value, args):
    pass

  def simulate(self,args):
    field = args.spaux().field
    if field:
        return True
    else:
        return False
    
  def logDensity(self,value,args):
    if self.population_name.startswith("precomputed"):
        probability_of_depencies = precomputed_CMIs[self.population_name]
    else: 
        raise ValueError("Stubbed - make sure string indicates precomputed CMI")
        probability_of_depencies = args.spaux().field
    if probability_of_depencies:
        dag = args.operandValues()[0]
        independence_keys = []
        for independence in get_independencies(dag):
            split_by_mid = independence.latex_string().split("\mid")
            if split_by_mid[-1]==" ":
                split_by_independence = split_by_mid[0].split(" \perp ")
                if "," in split_by_independence[1]:
                    for item in split_by_independence[1].split(","):
                        independence_keys.append((split_by_independence[0].strip(), item.strip()))
                else:
                    independence_keys.append((split_by_independence[0].strip(), split_by_independence[1].strip()))
            else:
                split_by_independence = split_by_mid[0].split(" \perp ")
                independence_keys.append(((split_by_independence[0].strip(), split_by_independence[1].strip()), split_by_mid[-1].strip()))

        logpdf = 0
        for key in probability_of_depencies.keys():
            if key in independence_keys:
                logpdf += np.log(1- probability_of_depencies[key])
            else:
                logpdf += np.log(probability_of_depencies[key])
    else:
        logpdf = 0
    return logpdf 


class MakerBDBPopulationOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    population_name = args.operandValues()[0]
    output = TypedPSP(BDBPopulationOutputPSP(population_name),
      SPType([t.ArrayUnboxedType(t.ArrayUnboxedType(t.BoolType()))], t.BoolType()))
    return VentureSPRecord(PopulationSP(NullRequestPSP(), output))



