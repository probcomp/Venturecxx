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

import venture.lite.gp as gp

#TODO clean up imports!
from collections import OrderedDict
from nose import SkipTest
from nose.tools import eq_
import numpy as np
import numpy.random as npr

from venture.test.config import broken_in
from venture.test.config import collectSamples
from venture.test.config import default_num_samples
from venture.test.config import get_ripl
from venture.test.config import in_backend
from venture.test.config import on_inf_prim
from venture.test.stats import reportKnownGaussian
from venture.test.stats import reportKnownMean
from venture.test.stats import reportPearsonIndependence
from venture.test.stats import statisticalTest
from venture.test.stats import stochasticTest
import venture.lite.covariance as cov
import venture.lite.gp as gp
import venture.lite.value as v

simplify_vnts_code = """
	assume simplify = (source) -> {
	  cond(        
	    (source[0] == "+")(["+", simplify(source[1]), simplify(source[2])]),
	    (source[0] == "*")(simplify_product(source)),
	    else(source))
	};"""

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_pattern_WNxWN():
    kernel1= ["WN", 2.] 
    kernel2= ["WN", 3.] 
    simplified_kernel = gp.pattern_matching_WNxWN(kernel1, kernel2)
    assert ["WN", 6.] == simplified_kernel 

def test_pattern_CxWN():
    kernel1= ["C", 4.] 
    kernel2= ["WN", 3.] 
    simplified_kernel = gp.pattern_matching_CxWN(kernel1, kernel2)
    assert ["WN", 12.] == simplified_kernel 

def test_pattern_CxC():
    kernel1= ["C", 2.] 
    kernel2= ["C", 3.] 
    simplified_kernel = gp.pattern_matching_CxC(kernel1, kernel2)
    assert ["C", 6.] == simplified_kernel 

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_flatten_product_base_case():
    simplified_kernel = gp.flatten_product(["WN",3.])
    assert [["WN", 3.]] == simplified_kernel 

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_flatten_product():
    flattened_product = gp.flatten_product(["*",["*",["WN", 1.],["SE",\
        2.]], ["*",["C", 3.],["WN", 4.]]])
    assert [["WN", 1.], ["SE", 2.],  ["C", 3.], ["WN", 4.]] == flattened_product

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_parse_to_tree_simple_case():
    flat_product = [["WN",1.]]
    parse_tree = gp.parse_to_tree(flat_product)
    assert ["WN", 1.] == parse_tree

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_parse_to_tree():
    flat_product = [["WN", 1.], ["SE", 2.],  ["C", 3.], ["WN", 4.]]
    parse_tree = gp.parse_to_tree(flat_product)
    assert ["*", ["WN", 1.0], ["*", ["SE", 2.0], ["*", ["C", 3.0], ["WN", 4.0]]]] == parse_tree


@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_base_case():
    simplified_kernel = gp.simplify_product(["WN",3.])
    assert ["WN",3.] == simplified_kernel 

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_simple_case():
    simplified_kernel = gp.simplify_product(["*",["WN",3.], ["WN",2.]])
    assert ["WN", 6.] == simplified_kernel 

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_Cs_WNs():
    simplified_kernel = gp.simplify_product(["*", ["WN", 1.0], ["*", ["C", 2.0], ["*", ["C", 3.0], ["WN", 4.0]]]])
    assert ["WN", 24.] == simplified_kernel 

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_Cs_WNs_RIPL():
    ripl = get_ripl()
    ripl.set_mode("venture_script")
    ripl.assume("source", """["*", ["WN", 1.0], ["*", ["C", 2.0], ["*", ["C", 3.0], ["WN", 4.0]]]]""")
    sampled_simplification = ripl.sample("simplify_product(source)")
    assert ["WN", 24.] == sampled_simplification


@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_in_sum():
    ripl = get_ripl()
    ripl.set_mode("venture_script")
    ripl.execute_program(simplify_vnts_code)
    ripl.assume("source", """
        ["+",
            ["*", ["WN", 1.0], ["*", ["C", 2.0], ["*", ["C", 3.0], ["WN", 4.0]]]],
            ["*", ["WN", 0.5], ["*", ["C", 2.0], ["*", ["C", 3.0], ["WN", 4.0]]]]]
        """)
    sampled_simplification = ripl.sample("simplify(source)")
    assert ["+",["WN", 24.], ["WN", 12.]] == sampled_simplification

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_heteroskedastic_RIPL():
    ripl = get_ripl()
    ripl.set_mode("venture_script")
    ripl.assume("source", """
        ["*",
            ["WN", 1.],
            ["*",
                ["*", ["LIN", 2.], 
                      ["WN", 3.]],
                ["WN", 4.]]]
    """)
    sampled_simplification = ripl.sample("simplify_product(source)")
    assert ["*", ["LIN", 2.], ["WN", 12.]] == sampled_simplification

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_SExWN_RIPL():
    ripl = get_ripl()
    ripl.set_mode("venture_script")
    ripl.assume("source", """
        ["*",
            ["WN", 3.],
            ["SE", 2.]]
    """)
    sampled_simplification = ripl.sample("simplify_product(source)")
    assert ["WN", 3.] == sampled_simplification

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_SExSE_RIPL():
    ripl = get_ripl()
    ripl.set_mode("venture_script")
    ripl.assume("source", """
        ["*",
            ["SE", 2.],
            ["SE", 3.]]
    """)
    sampled_simplification = ripl.sample("simplify_product(source)")
    assert ["SE", 6./5.] == sampled_simplification

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_WNxPER_RIPL():
    ripl = get_ripl()
    ripl.set_mode("venture_script")
    ripl.assume("source", """
        ["*",
            ["WN", 3.],
            ["PER", 4., 5.]]
    """)
    sampled_simplification = ripl.sample("simplify_product(source)")
    assert ["WN", 3.] == sampled_simplification

@broken_in("puma", "Puma does not define the gaussian process builtins")
@on_inf_prim("none")
def test_simplify_product_CxSExPERxWN_RIPL():
    ripl = get_ripl()
    ripl.set_mode("venture_script")
    ripl.assume("source", """
        ["*", 
            ["*",
                ["*",
                    ["WN", 1.],
                    ["PER", 2., 3.]],
                ["C", 4.]],
             ["SE", 5.]]
    """)
    sampled_simplification = ripl.sample("simplify_product(source)")
    assert ["WN", 4.] == sampled_simplification
#def test_create_gpmem_package_church():
#  ripl = get_ripl()
#  prep_ripl(ripl)
#  prog = """
#    [assume f (lambda (x) x)]
#    [assume package ((allocate_gpmem) f zero sq_exp)]
#  """
#  ripl.execute_program(prog)
