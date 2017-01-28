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
from venture.lite.psp import RandomPSP
from venture.lite.sp_help import typed_nr
from venture.lite.sp_help import deterministic_typed
import numpy as np

from pgmpy.models import BayesianModel

from venture.lite.causal_inference import *

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
        [t.StringType()], SPType([], t.BoolType())))
    ripl.bind_foreign_sp("dag_to_dot_notation",
            deterministic_typed(dag_to_dot_notation,
                [ 
                t.ArrayUnboxedType(t.ArrayUnboxedType(t.BoolType()))
                ],
                t.StringType(),
                min_req_args=1)
            )
    ripl.execute_program_from_file("examples/causal-inference/causal_inference.vnts") 

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
        assume observation_function = make_observation_function("precomputed_v_structure");""")

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_obervations_crash():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function("precomputed_v_structure");""")
    ripl.observe("observation_function(DAG)", True)

#@broken_in('puma', "Puma does not define the gaussian process builtins")
#@on_inf_prim('none')
#def test_inference_crash():
#    ripl = get_ripl()
#    ripl.assume("number_nodes", 3)
#    prep_ripl(ripl)
#    ripl.execute_program("""
#        assume observation_function = make_observation_function("precomputed_v_structure");""")
#    ripl.observe("observation_function(DAG)", True)
#    ripl.infer("mh(default, all, 1)")
#
#@broken_in('puma', "Puma does not define the gaussian process builtins")
#@on_inf_prim('none')
#def test_inference_independent_mh_2_nodes():
#    ripl = get_ripl()
#    ripl.assume("number_nodes", 2)
#    prep_ripl(ripl)
#    ripl.execute_program("""
#        assume observation_function = make_observation_function("precomputed_independent_nodes");""")
#    ripl.observe("observation_function(DAG)", True)
#    ripl.infer("mh(default, all, 100)")
#    sample = ripl.sample("dag_to_dot_notation(DAG)")
#    assert sample == ""

#@broken_in('puma', "Puma does not define the gaussian process builtins")
#@on_inf_prim('none')
#def test_inference_simple_link_mh_2_nodes():
#    ripl = get_ripl()
#    ripl.assume("number_nodes", 2)
#    prep_ripl(ripl)
#    ripl.execute_program("""
#        assume observation_function = make_observation_function("precomputed_simple_link_2_nodes");""")
#    ripl.observe("observation_function(DAG)", True)
#    ripl.infer("mh(default, all, 100)")
#    sample = ripl.sample("dag_to_dot_notation(DAG)")
#    assert (sample == "(0)-->(1), ") or (sample == "(1)-->(0), ")
#    
@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_simple_link_mh_3_nodes():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function("precomputed_simple_link");""")
    ripl.observe("observation_function(DAG)", True)
    ripl.infer("mh(default, all, 50)")
    sample = ripl.sample("dag_to_dot_notation(DAG)")
    assert (sample == "(0)-->(2), ") or (sample == "(2)-->(0), ")
   

@broken_in('puma', "Puma does not define the gaussian process builtins")
@on_inf_prim('none')
def test_inference_v_struct_mh():
    ripl = get_ripl()
    ripl.assume("number_nodes", 3)
    prep_ripl(ripl)
    ripl.execute_program("""
        assume observation_function = make_observation_function("precomputed_v_structure");""")
    ripl.observe("observation_function(DAG)", True)
    ripl.infer("mh(default, all, 50)")
    sample = ripl.sample("dag_to_dot_notation(DAG)")
    assert (sample == "(0)-->(2), (1)-->(2), ") or (sample == "(1)-->(2), (2)-->(2), ")
