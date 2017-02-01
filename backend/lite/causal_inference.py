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


def create_cmi_query(column1, column2, population_name, evidence=None, number_models=30,
                         threshold=0.05, number_of_samples=100):
    """ Creat queries needed for CMI """

    query_dict= {
        "column1": column1,
        "column2": column2,
        "population_name": population_name,
        "evidence": evidence,
        "number_models": number_models,
        "number_of_samples": number_of_samples,
        "threshold": threshold,
        }
    if not evidence:
        drop_existing_table = "DROP TABLE IF EXISTS 'mi({column1}, {column2})';".format(**query_dict)
        create_mi_table = """
            CREATE TABLE  'mi({column1}, {column2})' AS
            SIMULATE
                MUTUAL INFORMATION OF {column1} WITH {column2}
                USING {number_of_samples} SAMPLES
                AS 'mi' FROM MODELS OF {population_name};""".format(**query_dict)
        get_probability = """SELECT COUNT(mi)*1.0/{number_models} AS value
            FROM 'mi({column1}, {column2})' WHERE temp>{threshold}""".format(**query_dict)
    else:
        drop_existing_table = "DROP TABLE IF EXISTS 'mi({column1}, {column2} | {evidence})';".format(**query_dict)
        create_mi_table = """
            CREATE TABLE  'mi({column1}, {column2})' AS
            SIMULATE
                MUTUAL INFORMATION OF {column1} WITH {column2}
                GIVEN ({evidence})
                USING {number_of_samples} SAMPLES
                AS 'mi' FROM MODELS OF {population_name};""".format(**query_dict)
        get_probability = """SELECT COUNT(mi)*1.0/{number_models} AS value
            FROM 'mi({column1}, {column2} | {evidence})' WHERE temp>{threshold}""".format(**query_dict)


    return [drop_existing_table, create_mi_table, get_probability]


def get_all_possible_dependencies(list_of_all_nodes):
    statements_mutual_information = []
    for i,node in enumerate(list_of_all_nodes):
        for other_node in list_of_all_nodes[i:]:
            if node!=other_node :
                statements_mutual_information.append((node, other_node))
                
    statements_conditional_mutual_information = []
    for mi_statement in statements_mutual_information:
        for node in list_of_all_nodes:
            if node!=mi_statement[0] and node!=mi_statement[1]:
     			statements_conditional_mutual_information.append((
                        mi_statement, node))
    
    return statements_mutual_information +\
		statements_conditional_mutual_information

def get_cmi_queries(list_of_all_nodes, population_name):
    list_of_dependencies = get_all_possible_dependencies(list_of_all_nodes)
    cmi_queries = []
    for dependence in list_of_dependencies:
        if  isinstance(dependence[0], basestring):
            cmi_queries.append(create_cmi_query(dependence[0], dependence[1],
                population_name))
        else:
            cmi_queries.append(create_cmi_query(dependence[0][0],
                dependence[0][1], population_name,
                evidence=dependence[1]))
    return cmi_queries

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



