from venture.test.config import broken_in

from nose.tools import nottest
import test.inference_quality.micro.gp_programs as gp_programs

from test.inference_quality.micro.gp_testing_utils import *
############################################################
#	    Testing CxWN kernel
#
############################################################

# Smoke Test
@broken_in('puma', "Puma does not define the Gaussian process builtins")
def test_hyper_inf_WN_smoke():
  """ Testing interpolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 100
  noise_std = 2

  return gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, smoke_test, \
    inference_prog= inf_prog)


# Intrapolation
@broken_in('puma', "Puma does not define the Gaussian process builtins")
@statisticalTest
def test_hyper_inf_WN_interpolation():
  """ Testing interpolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 100
  noise_std = 2
  
  return gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, ks_posterior_samples_interpolation, \
    inference_prog= inf_prog)

# Extrapolation
@broken_in('puma', "Puma does not define the Gaussian process builtins")
@statisticalTest
def test_hyper_inf_WN_extrapolation():
  """ Testing extrapolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 100
  noise_std = 2

  return gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, ks_posterior_samples_extrapolation, \
    inference_prog= inf_prog)

# Extrapolation - look at mean - does not makes sense here, just for
# illustration
@broken_in('puma', "Puma does not define the Gaussian process builtins")
@statisticalTest
def test_hyper_inf_WN_extrapolation_mean():
  """ Testing extrapolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 100
  noise_std = 0.316 

  return gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, mean_posterior_samples_extrapolation, \
    inference_prog= inf_prog)

# Plot posterior for visual inspection
@broken_in('puma', "Puma does not define the Gaussian process builtins")
def test_WN_posterior_plot():
  " Testing that SE log score is below 0 before inference " 
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 100
  noise_std = 2

  return gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, produce_plots, \
    inference_prog= inf_prog)



# Smoke Test numerical issues with LogDensityOfCounts
@broken_in('puma', "Puma does not define the Gaussian process builtins")
def test_global_log_joint_smoke_WN():
  """ Testing for very large values LogDensityOfCounts some kernel
  configurations caused problems related to this"""
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 100
  noise_std = 2

  return gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, test_global_log_joint_smoke, \
    inference_prog= inf_prog)



############################################################
#	   Using a different program and fix an experimental 
#          condition
############################################################
# Intrapolation with a fixed mean
@broken_in('puma', "Puma does not define the Gaussian process builtins")
@statisticalTest
def test_hyper_inf_interpolation_with_fixed_mean():
  """ Testing interpolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CplusCxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", 0, 100)"""
  n_datapoints = 100
  noise_std = 2
  observations = ["observe mean_line = 5;"] 

  # f_constant(x) = 5 
  return gp_test_skeleton(f_constant, n_datapoints, noise_std, ripl, ks_posterior_samples_interpolation, \
    inference_prog= inf_prog, obs_statements = observations)

############################################################
#	   Sanity Checks- remove @nottest and they should fail 
#
############################################################

# remove not-test for sanity checking. This should fail!
@broken_in('puma', "Puma does not define the Gaussian process builtins")
@statisticalTest
@nottest
def test_hyper_inf_interpolation_with_fixed_wrong_mean():
  """ Testing interpolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CplusCxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", 0, 100)"""
  n_datapoints = 100
  noise_std = 2
  observations = ["observe mean_line = 20;"] 

  # f_constant(x) = 5 
  return gp_test_skeleton(f_constant, n_datapoints, noise_std, ripl, ks_posterior_samples_interpolation, \
    inference_prog= inf_prog, obs_statements = observations)
@nottest
@broken_in('puma', "Puma does not define the Gaussian process builtins")
def test_hyper_inf_WN_interpolation_wrong_std():
  """ Testing interpolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 100
  noise_std = 5
  return gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, ks_posterior_samples_interpolation, \
    inference_prog= inf_prog)

@broken_in('puma', "Puma does not define the Gaussian process builtins")
@nottest
def test_WN_posterior_plot_noObs():
  " Testing that SE log score is below 0 before inference " 
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 0 # no observations
  noise_std = 2

  return gp_test_skeleton(f_zero, n_datapoints , noise_std, ripl, produce_plots, \
    inference_prog= inf_prog)

@broken_in('puma', "Puma does not define the Gaussian process builtins")
@nottest
def test_WN_posterior_plot_noInf():
  " Testing that SE log score is below 0 before inference " 
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)

  n_datapoints = 100
  noise_std = 2

  return gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, produce_plots)

# remove not-test for sanity checking. This should fail!
@broken_in('puma', "Puma does not define the Gaussian process builtins")
@nottest
def test_hyper_inf_WN_interpolation_noINf():
  """ Testing interpolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  gp_test_skeleton(f_zero, n_datapoints, noise_std, ripl, ks_posterior_samples_interpolation)

@broken_in('puma', "Puma does not define the Gaussian process builtins")
@nottest
def test_hyper_inf_WN_interpolation_noObs():
  """ Testing interpolation statistically with an CxWN kernel and using the known
  Gaussian"""
  prog = gp_programs.simple_CxWN
  ripl = prep_ripl(prog)
  
  inf_prog = """mh("hyper", one, 100)"""
  n_datapoints = 0 # no observations
  noise_std = 2

  return gp_test_skeleton(f_zero, n_datapoints , noise_std, ripl, ks_posterior_samples_interpolation, \
    inference_prog= inf_prog)
