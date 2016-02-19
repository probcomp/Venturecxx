
__author__ = 'ulli'

import numpy as np
from venture import shortcuts

from venture.test.config import in_backend, broken_in   
from venture.test.stats import statisticalTest, reportKnownGaussian
#from venture.test.config import broken_in

# so far, I am only testing with VenChurch syntax and ripl-API. I guess that
# once the syntax thing is resolved, these tests should cover both syntaxes
def init_ripl(venChurch=None):
    if venChurch is None:
	venChurch = False
    ''' 
    initialize ripl 
    '''
    ripl = shortcuts.make_lite_ripl()
    if venChurch:
	ripl.set_mode("church_prime")
    ripl.assume("x",1)
    return ripl


# simple smoke tests

@broken_in("puma", "Does neither support assume_values nor GPs yet")
@in_backend("lite")
def test_compound_assume_smoke():

    smoke_prog ="""

    [assume a_ref (ref (uniform_discrete 2 3))]
    [assume b_ref (ref (uniform_discrete 3 4))]
    (assume_values (a b) (list  a_ref b_ref))
    
    [assume l (list a_ref b_ref)]
    (assume_values (c  d ) l)

    [assume y 10]
    (assume_values ( u )  (list (ref (uniform_discrete 20 21))))

    """
    ripl = init_ripl(venChurch=True)
    ripl.execute_program(smoke_prog)


    assert ripl.sample("x") == 1, "simple assume does not work"
    assert ripl.sample("y") == 10, "simple assume does not work"

    assert ripl.sample("a") == 2, "compound assume does not work, first component"
    assert ripl.sample("b") == 3, "compound assume does not work, second component"

    assert ripl.sample("c") == 2, "compound assume does not work, first component, symbol instead of list"
    assert ripl.sample("d") == 3, "compound assume does not work, second component"
    
    assert ripl.sample("u") == 20, "compound assume does not work for a one-element-compound"


# testing observations
@broken_in("puma", "Does neither support assume_values nor GPs yet")
@in_backend("lite")
def test_compound_assume_observations():

    obs_prog ="""

    [assume a_ref (ref (normal 0 1))]
    [assume b_ref (ref (normal 0 1))]
    [assume l (list  a_ref b_ref)]
    (assume_values (a b) l)


    """
    ripl = init_ripl(venChurch=True)

    ripl.execute_program(obs_prog)

    ripl.observe("(deref a_ref)",1)

    assert ripl.sample("(deref a_ref)") == 1, "simple a_ref is not observed"
    assert ripl.sample("a") == 1, "first element compund is not observed"
    assert ripl.sample("(deref (first  l ) )") == 1, "first compound list item is not observed"
    assert ripl.sample("(deref (second l ) )") != 1, "confused second and first compound element"
    assert ripl.sample("(deref b_ref)") != 1, "confused second and first compound element"
    assert ripl.sample("b") != 1, "second element compound is confused with first"

    ripl.observe("b",2)

    assert ripl.sample("b") == 2, "second element compound is not observed"
    assert ripl.sample("(deref a_ref)") == 1, "second observation made the first incorrect"
    assert ripl.sample("(deref (first  l) )") == 1, "second observation made the first incorrect"
    assert ripl.sample("(deref (second l ) )") == 2, "deref of second list item is not observed"
    assert ripl.sample("(deref b_ref)") == 2, "deref of second ref is not observed"


# testing inference
@broken_in("puma", "Does neither support assume_values nor GPs yet")
@in_backend("lite")
def test_compound_assume_inf_happening():
    inf_test_prog ="""

    [assume a_ref (tag (quote a_scope ) 0 (ref (normal 0 10)))]
    [assume b_ref (tag (quote b_scope ) 0 (ref (normal -10 10)))]
    [assume l (list  a_ref b_ref)]
    (assume_values (a b) l)

    [assume obs_1 (lambda ( )  (normal a 1))]
    [assume obs_2 (lambda ( )  (normal b 1))]

    """

    ripl = init_ripl(venChurch=True)

    ripl.execute_program(inf_test_prog)

    previous_value = ripl.sample("b")

    for i in range(20):
	ripl.observe("(obs_1)",np.random.normal(5,0.1))

    ripl.infer("(mh (quote a_scope ) 0 100)")


    assert ripl.sample("b") == previous_value, "inferred to wrong part of the compound"
    
    for i in range(20):
	ripl.observe("(obs_2)",np.random.normal(-15,0.1))

    ripl.infer("(mh (quote b_scope ) 0 100)")


    assert ripl.sample("b") != previous_value, "inferred for second part didn't work"


@broken_in("puma", "Does neither support assume_values nor GPs yet")
@statisticalTest
@in_backend("lite")
def test_compound_assume_inf_first_element():
    inf_test_prog ="""

    [assume a_ref (tag (quote a_scope ) 0 (ref (normal 0 10)))]
    [assume b_ref (tag (quote b_scope ) 0 (ref (normal -10 10)))]
    [assume l (list  a_ref b_ref)]
    (assume_values (a b) l)

    [assume obs_1 (lambda ( )  (normal a 1))]
    [assume obs_2 (lambda ( )  (normal b 1))]

    """

    ripl = init_ripl(venChurch=True)

    ripl.execute_program(inf_test_prog)

    previous_value = ripl.sample("b")

    for i in range(20):
	ripl.observe("(obs_1)",np.random.normal(5,1))

    ripl.infer("(mh (quote a_scope ) 0 100)")
    
    # just read test/config.py - this should use collectSamples 
    post_samples = [ripl.sample("(obs_1)")for i in range(30)]

	 
    return reportKnownGaussian(5,1,post_samples)

@broken_in("puma", "Does neither support assume_values nor GPs yet")
@statisticalTest
@in_backend("lite")
def test_compound_assume_inf_second_element():
    inf_test_prog ="""

    [assume a_ref (tag (quote a_scope ) 0 (ref (normal 0 10)))]
    [assume b_ref (tag (quote b_scope ) 0 (ref (normal -10 10)))]
    [assume l (list  a_ref b_ref)]
    (assume_values (a b) l)

    [assume obs_1 (lambda ( )  (normal a 1))]
    [assume obs_2 (lambda ( )  (normal b 1))]

    """

    ripl = init_ripl(venChurch=True)

    ripl.execute_program(inf_test_prog)

    previous_value = ripl.sample("b")

    for i in range(20):
	ripl.observe("(obs_1)",np.random.normal(5,0.1))

    ripl.infer("(mh (quote a_scope ) 0 100)")


    for i in range(20):
	ripl.observe("(obs_2)",np.random.normal(-15,0.1))

    ripl.infer("(mh (quote b_scope ) 0 100)")

    # just read test/config.py - this should use collectSamples 
    post_samples = [ripl.sample("(obs_2)")for i in range(30)]

	 
    return reportKnownGaussian(-15,0.1,post_samples)


test_compound_assume_smoke()
test_compound_assume_observations()
test_compound_assume_inf_happening()
