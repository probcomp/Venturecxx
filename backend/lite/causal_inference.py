import numpy as np
import matplotlib.pyplot as plt

from pgmpy.models import BayesianModel

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

import bayeslite
from bayeslite import bayesdb_open
from iventure.utils_bql import query

import sys
sys.path.insert(0, '/scratch/ulli/Venturecxx/examples/causal-inference')

from precomputed_cmi import precomputed_CMIs

def dag_to_dot_notation(dag, list_of_node_names):
    output_str = ""
    for i in range(len(dag)): 
        for j in range(len(dag)):
            if dag[i][j]:
                output_str+="(%s)-->(%s), " % (list_of_node_names[i], list_of_node_names[j],)
    return output_str


def get_independencies(dag, list_of_node_names):
    # convert to pgmpy representation
    edges_pgmpy = []
    for i in range(len(dag)):
        for j in range(len(dag)):
            if dag[i][j]:
                edges_pgmpy.append((list_of_node_names[i], list_of_node_names[j]))
    b_net_model = BayesianModel()
    b_net_model.add_nodes_from(list_of_node_names) 
    b_net_model.add_edges_from(edges_pgmpy) 
    pgmpy_independencies_object = b_net_model.get_independencies()
    return pgmpy_independencies_object.independencies


def create_cmi_query(column1, column2, population_name, evidence=None, number_models=30,
                         number_of_samples=100):
    """ Creat queries needed for CMI """

    query_dict= {
        "column1": column1,
        "column2": column2,
        "population_name": population_name,
        "evidence": evidence,
        "number_models": number_models,
        "number_of_samples": number_of_samples,
        }
    if not evidence:
        drop_existing_table = """DROP TABLE IF EXISTS mi_{column1}_{column2};""".format(**query_dict)
        create_mi_table = """CREATE TABLE  mi_{column1}_{column2} AS
            SIMULATE
                MUTUAL INFORMATION OF {column1} WITH {column2}
                USING {number_of_samples} SAMPLES
                AS mi FROM MODELS OF {population_name};""".format(**query_dict)
    else:
        drop_existing_table = """DROP TABLE IF EXISTS mi_{column1}_{column2}_given_{evidence};""".format(**query_dict)
        create_mi_table = """CREATE TABLE  mi_{column1}_{column2}_given_{evidence} AS
            SIMULATE
                MUTUAL INFORMATION OF {column1} WITH {column2}
                GIVEN ({evidence})
                USING {number_of_samples} SAMPLES
                AS mi FROM MODELS OF {population_name};""".format(**query_dict)

        
    return [drop_existing_table, create_mi_table]

def get_probability_of_cmi_query(column1, column2, number_models, evidence=None,
    threshold=0.1):

    query_dict= {
        "column1": column1,
        "column2": column2,
        "evidence": evidence,
        "number_models": number_models,
        "threshold": threshold,
        }
    if evidence:
        get_probability_query = """SELECT COUNT(mi)*1.0/{number_models} AS value
            FROM mi_{column1}_{column2}_given_{evidence} WHERE mi>{threshold}""".format(**query_dict)
    else:
        get_probability_query = """SELECT COUNT(mi)*1.0/{number_models} AS value
            FROM mi_{column1}_{column2} WHERE mi>{threshold}""".format(**query_dict)

    return get_probability_query


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
            cmi_queries.extend(create_cmi_query(dependence[0], dependence[1],
                population_name))
        else:
            cmi_queries.extend(create_cmi_query(dependence[0][0],
                dependence[0][1], population_name,
                evidence=dependence[1]))
    return cmi_queries

def get_cmi_probabilities(list_of_all_nodes, number_models):
    list_of_dependencies = get_all_possible_dependencies(list_of_all_nodes)
    cmi_probabilities = []
    for dependence in list_of_dependencies:
        if  isinstance(dependence[0], basestring):
            cmi_probabilities.append((dependence,
                get_probability_of_cmi_query(dependence[0], dependence[1], number_models)))
        else:
            cmi_probabilities.append((dependence,
                get_probability_of_cmi_query(dependence[0][0], dependence[0][1],
                number_models, evidence=dependence[1])))
    return cmi_probabilities


class PopulationSPAux(SPAux):
  def __init__(self):
    self.result_dict_p_cmi_queries = {} 
    self.list_of_cmi_queries = [] 

  def copy(self):
    aux = PopulationSPAux()
    aux.result_dict_p_cmi_queries = self.result_dict_p_cmi_queries
    aux.list_of_cmi_queries = self.list_of_cmi_queries
    return aux




class PopulationSP(SP):
  def constructSPAux(self):
    return PopulationSPAux()

  def show(self,spaux):
    return spaux.result_dict_p_cmi_queries



class BDBPopulationOutputPSP(RandomPSP):

  def __init__(self, population_name, metamodel_name, bdb_file_path):
    self.population_name = population_name 
    self.metamodel_name = metamodel_name
    self.bdb_file_path = bdb_file_path 

  def _query_bdb(self, list_of_cmi_queries, list_of_all_nodes): 
    if self.metamodel_name.startswith("precomputed"):
        result_dict_p_cmi_queries = precomputed_CMIs[self.metamodel_name]
    else:
        #print >> sys.stderr, "########################" 
        bdb = bayesdb_open(self.bdb_file_path)
        population_id = bayeslite.core.bayesdb_get_population(bdb, self.population_name)
        generator_id = bayeslite.core.bayesdb_get_generator(bdb, population_id, self.metamodel_name)
        number_models = len(bayeslite.core.bayesdb_generator_modelnos(bdb,
            generator_id))
        #print >> sys.stderr, "self.list_of_cmi_queries"
        #print >> sys.stderr, self.list_of_cmi_queries
        #print >> sys.stderr, "self.list_of_all_nodes"
        #print >> sys.stderr, self.list_of_all_nodes
        #print >> sys.stderr, "number_models"
        #print >> sys.stderr, number_models
        for cmi_query in list_of_cmi_queries:
            print "Running the following query:"
            print cmi_query
            query(bdb, cmi_query) # Drop table if exists
        result_dict_p_cmi_queries = {}
        for cmi_probability_dict_key, probability_cmi in get_cmi_probabilities(
            list_of_all_nodes, number_models):
            #print >> sys.stderr, "------------------------" 
            #print >> sys.stderr, "probability_cmi"
            #print >> sys.stderr,probability_cmi
            result = query(bdb, probability_cmi)["value"].loc[0]
            if result==1.:
                result -= 0.00000001 #in case it's exactly 1.
            elif result==0.: 
                result += 0.00000001 #in case it's exactly 0.
            #print >> sys.stderr, "result"
            #print >> sys.stderr, result
            result_dict_p_cmi_queries[cmi_probability_dict_key] = result
            
        #print >> sys.stderr, "result_dict_p_cmi_queries"
        #print >> sys.stderr, result_dict_p_cmi_queries 
        # TODO close stream for bdb file
    return result_dict_p_cmi_queries 

  def logDensity(self,value,args):

    spaux = args.spaux()
    dag = args.operandValues()[0]
    list_of_all_nodes = args.operandValues()[1]
    list_of_cmi_queries = value
    #print >> sys.stderr, "-------------- logDensity -------------"
    #print >> sys.stderr, "spaux.result_dict_p_cmi_queries"
    #print >> sys.stderr, spaux.result_dict_p_cmi_queries
    #print >> sys.stderr, "---------------------------"
    if not spaux.result_dict_p_cmi_queries:
        spaux.result_dict_p_cmi_queries  =\
            self._query_bdb(list_of_cmi_queries, list_of_all_nodes)
    result_dict_p_cmi_queries = spaux.result_dict_p_cmi_queries

    if result_dict_p_cmi_queries:
        independence_keys = []
        for independence in get_independencies(dag, list_of_all_nodes):
            #print >> sys.stderr, "independence" 
            #print >> sys.stderr, independence
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
        #print >> sys.stderr, "independence_keys" 
        #print >> sys.stderr, independence_keys
        for key in result_dict_p_cmi_queries.keys():
            if key in independence_keys:
                #print >> sys.stderr, "flipped key" 
                #print >> sys.stderr, key
                logpdf += np.log(1- result_dict_p_cmi_queries[key])
            else:
                #print >> sys.stderr, "kept key" 
                #print >> sys.stderr, key
                logpdf += np.log(result_dict_p_cmi_queries[key])
    else:
        logpdf = 0
    #print >> sys.stderr, "DAG:"
    #print >> sys.stderr, dag_to_dot_notation(dag, self.list_of_all_nodes)
    #print >> sys.stderr, "np.exp(logpdf)"
    #print >> sys.stderr, np.exp(logpdf)
    #print >> sys.stderr, "########################" 
    return logpdf 

  def incorporate(self, value, args):
    spaux = args.spaux()
    if value and not spaux.result_dict_p_cmi_queries:
        spaux = args.spaux()
        spaux.list_of_cmi_queries = value
        list_of_all_nodes = args.operandValues()[1]
        #print >> sys.stderr, "######## incorporate ######"
        #print >> sys.stderr,  "value"
        #print >> sys.stderr,  value
        #print >> sys.stderr,  "spaux.result_dict_p_cmi_queries"
        #print >> sys.stderr,  spaux.result_dict_p_cmi_queries
        #print >> sys.stderr, "########################" 
        spaux.result_dict_p_cmi_queries = self._query_bdb(value, list_of_all_nodes)
    


  def unincorporate(self, value, args):
    pass

  def simulate(self,args):
    list_of_cmi_queries = args.spaux().result_dict_p_cmi_queries
    return list_of_cmi_queries


class MakerBDBPopulationOutputPSP(DeterministicMakerAAAPSP):
  def simulate(self, args):
    population_name = args.operandValues()[0]
    metamodel_name = args.operandValues()[1]
    bdb_file_path = args.operandValues()[2]
    output = TypedPSP(BDBPopulationOutputPSP(population_name, metamodel_name,
        bdb_file_path),
      SPType([t.ArrayUnboxedType(t.ArrayUnboxedType(t.BoolType())),
          t.ArrayUnboxedType(t.StringType())],
          t.ArrayUnboxedType(t.StringType())))
    return VentureSPRecord(PopulationSP(NullRequestPSP(), output))

