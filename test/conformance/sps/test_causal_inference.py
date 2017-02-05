# Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
#
# This file is part of Venture.
#
# Venture is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Venture is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Venture.  If not, see <http://www.gnu.org/licenses/>.
from nose import SkipTest
from nose.tools import eq_
import numpy as np

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.config import in_backend
from venture.test.config import on_inf_prim
from venture.test.stats import statisticalTest
from venture.test.stats import stochasticTest
import venture.lite.value as v
import venture.lite.types as t
from venture.lite.sp import SPType
from venture.lite.psp import RandomPSP
from venture.lite.sp_help import typed_nr
from venture.lite.sp_help import deterministic_typed
import numpy as np

from pgmpy.models import BayesianModel

from venture.lite.causal_inference import MakerBDBPopulationOutputPSP 
from venture.lite.causal_inference import dag_to_dot_notation
from venture.lite.causal_inference import get_cmi_queries

def prep_ripl(ripl):
    ripl.set_mode("venture_script")
    ripl.bind_foreign_sp("pop",
            deterministic_typed(lambda l,i: [v.VentureNumber(l.pop(i)), 
                v.VentureArray([v.VentureNumber(item) for item in l])],
                [ 
                t.ArrayUnboxedType(t.NumberType()), 
                t.IntegerType(),
                ],
                t.ArrayUnboxedType(t.AnyType(), t.ArrayType()),
                min_req_args=2)
            )
    ripl.bind_foreign_sp("make_observation_function", typed_nr(MakerBDBPopulationOutputPSP(),
        [
            t.StringType(),
            t.StringType(),
            t.StringType(),
        ],
        SPType([], t.ArrayUnboxedType(t.StringType()))))
    ripl.bind_foreign_sp("dag_to_dot_notation",
            deterministic_typed(dag_to_dot_notation,
                [ 
                t.ArrayUnboxedType(t.ArrayUnboxedType(t.BoolType())),
                t.ArrayUnboxedType(t.StringType())
                ],
                t.StringType(),
                min_req_args=1)
            )
    ripl.bind_foreign_inference_sp("get_cmi_queries",
            deterministic_typed(get_cmi_queries,
                [ 
                t.ArrayUnboxedType(t.StringType()),
                t.StringType(),
                ],
                t.ArrayUnboxedType(t.StringType()),
                min_req_args=1)
            )
    ripl.execute_program_from_file("examples/causal-inference/causal_inference.vnts") 

# TODO: Find out if this is this REALLY broken in puma.
@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_model_crash():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_create_obervation_function_crash():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function =
            make_observation_function("non_existing_population_name",
            "precomputed_v_structure", "non_existing.bdb");""")

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_obervations_crash():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function(
            "non_existing_population_name",
            "precomputed_v_structure", "non_existing.bdb");""")
    ripl.execute_program("""observe observation_function(DAG, ["x", "y", "z"]) = []""")


@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_fixed_cmi_crash():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function(
            "non_existing_population_name",
            "precomputed_v_structure", "non_existing.bdb");""")
    ripl.execute_program("""observe observation_function(DAG, ["x", "y", "z"]) = []""")
    ripl.infer("mh(default, all, 1)")

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_fixed_cmi_independent_mh_2_nodes():
    ripl = get_ripl()
    ripl.assume("number_nodes", 2)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function(
            "non_existing_population_name",
            "precomputed_independent_nodes",
            "non_existing.bdb");""")
    ripl.execute_program("""observe observation_function(DAG, ["x", "y"]) = []""")
    ripl.infer("mh(default, all, 150)")
    sample = ripl.sample("""dag_to_dot_notation(DAG, ["x", "y"])""")
    assert sample == ""

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_fixed_cmi_simple_link_mh_2_nodes():
    ripl = get_ripl()
    ripl.assume("number_nodes", 2)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function(
            "non_existing_population_name",
            "precomputed_simple_link_2_nodes",
            "non_existing.bdb");""")
    ripl.execute_program("""observe observation_function(DAG, ["x", "y"]) = []""")
    ripl.infer("mh(default, all, 150)")
    sample = ripl.sample("""dag_to_dot_notation(DAG, ["x", "y"])""")
    assert (sample == "(x)-->(y), ") or (sample == "(y)-->(x), ")
#    
@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_fixed_cmi_simple_link_mh_3_nodes():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function(
            "non_existing_population_name",
            "precomputed_simple_link",
            "non_existing.bdb");""")
    ripl.execute_program("""observe observation_function(DAG, ["x", "y", "z"]) = []""")
    ripl.infer("mh(default, all, 150)")
    sample = ripl.sample("""dag_to_dot_notation(DAG, ["x", "y", "z"])""")
    assert (sample == "(x)-->(z), ") or (sample == "(z)-->(x), ")
   

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_fixed_cmi_v_struct_mh():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function(
            "non_existing_population_name",
            "precomputed_v_structure",
            "non_existing.bdb");""")
    ripl.execute_program("""observe observation_function(DAG, ["x", "y", "z"]) = []""")
    ripl.infer("mh(default, all, 50)")
    sample = ripl.sample("""dag_to_dot_notation(DAG, ["x", "y", "z"])""")
    assert (sample == "(x)-->(z), (y)-->(z), ") or (sample == "(y)-->(z), (x)-->(z), ")

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_cmi_crash():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function(
            "non_existing_population_name",
            "precomputed_v_structure",
            "non_existing.bdb");""")
    ripl.execute_program("""observe observation_function(DAG, ["x", "y", "z"]) = []""")
    list_of_queries = ripl.infer("""return(get_cmi_queries(["x", "y", "z"], "causal_population"))""")

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_cmi_correct_length():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    list_of_queries = ripl.infer("""return(get_cmi_queries(["x", "y", "z"], "causal_population"))""")
    # checking that we have total of 6 mi queries + 6 x "DROP TABLE IF EXISTS"
    assert len(list_of_queries) == 12 

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_obs_function_with_cmi_crash():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        define list_of_cmi_queries = get_cmi_queries(["x", "y", "z"], "causal_population");
        define list_of_nodes = ["x", "y", "z"];
        """)
    ripl.execute_program("""
        assume observation_function = make_observation_function(
            "non_existing_population_name",
            "precomputed_v_structure",
            "non_existing.bdb"
            );
        """)
    ripl.execute_program("""
        observe observation_function(DAG, ${list_of_nodes}) = list_of_cmi_queries;""")

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_causal_inference_crash():
    ripl = get_ripl()
    ripl.assume("number_nodes", 2)
    prep_ripl(ripl)
    ripl.execute_program("""
        define list_of_nodes = ["x", "y"];
        define list_of_cmi_queries = get_cmi_queries(list_of_nodes, "commonp")
        """)
    #FIXME re-run data-generator and fix naming of generator and population
    ripl.execute_program("""
        assume observation_function = make_observation_function(
                                      "commonp",
                                      "commonm",
                                      "examples/causal-inference/common_faithful.bdb"
                                      );""")
    ripl.execute_program("""
        observe observation_function(DAG, ${list_of_nodes}) = list_of_cmi_queries;""")
    ripl.infer("mh(default, all, 1)")

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_independent_mh_2_nodes():
    ripl = get_ripl()
    ripl.assume("number_nodes", 2)
    prep_ripl(ripl)
    ripl.execute_program("""
        define list_of_nodes = ["x", "y"];
        define list_of_cmi_queries = get_cmi_queries(list_of_nodes, "commonp")
        """)
    #FIXME re-run data-generator and fix naming of generator and population
    ripl.execute_program("""
        assume observation_function = make_observation_function(
                                      "commonp",
                                      "commonm",
                                      "examples/causal-inference/common_faithful.bdb"
                                      );""")
    ripl.execute_program("""
        observe observation_function(DAG, ${list_of_nodes}) = list_of_cmi_queries;""")
    ripl.infer("mh(default, all, 100)")

    n_samples = 10
    all_samples = [] 
    for _ in range(n_samples):
        ripl.infer("mh(default, all, 1)")
        all_samples.append(ripl.sample("""dag_to_dot_notation(DAG, ["x", "y"])"""))
    all_samples = np.array(all_samples)
    assert (float(sum(all_samples == ""))/n_samples) > 0.7 

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_simple_link_mh_2_nodes():
    ripl = get_ripl()
    ripl.assume("number_nodes", 2)
    prep_ripl(ripl)
    ripl.execute_program("""
        define list_of_nodes = ["x", "z"];
        define list_of_cmi_queries = get_cmi_queries(list_of_nodes, "commonp")
        """)
    #FIXME re-run data-generator and fix naming of generator and population
    ripl.execute_program("""
        assume observation_function = make_observation_function(
                                      "commonp",
                                      "commonm",
                                      "examples/causal-inference/common_faithful.bdb"
                                      );""")
    ripl.execute_program("""
        observe observation_function(DAG, ${list_of_nodes}) = list_of_cmi_queries;""")
    ripl.infer("mh(default, all, 10)")

    n_samples = 10
    all_samples = [] 
    for _ in range(n_samples):
        ripl.infer("mh(default, all, 1)")
        all_samples.append(ripl.sample("""dag_to_dot_notation(DAG, ["x", "z"])"""))
    all_samples = np.array(all_samples)
    count_correct_dag = float(sum(all_samples == "(x)-->(z), ")) + float(sum(all_samples == "(z)-->(x), "))
    assert (count_correct_dag /n_samples) > 0.7 
