import datetime

import venture.lite.types as t
from venture.lite.sp_help import deterministic_typed
from venture.test.config import get_ripl, broken_in, collectSamples
from venture.test.stats import reportKnownMean, statisticalTest, reportKnownGaussian
import  venture.lite.value as vv 
import numpy as np

from nose.tools import nottest
import seaborn as sns
import matplotlib.pyplot as plt
import test.inference_quality.micro.gp_programs as gp_programs
# Possible data-generating functions
@np.vectorize
def f_lin(x):
    return x
@np.vectorize
def f_zero(x):
    x = 0
    return x
@np.vectorize
def f_constant(x):
    x = 5
    return x
@np.vectorize
def f_per(x):
    return 10* np.sin(0.5 * x)
@np.vectorize
def f_lin_plus_per(x):
    return f_lin(x) + f_per(x)

def rmse(target,predicted):
    return np.sqrt(np.mean((target - predicted)**2))



def array(xs):
  return vv.VentureArrayUnboxed(np.array(xs),  t.NumberType())

def generate_synthetic_data(data_generating_function,n,std, x_min = None, x_max= None):
  if (x_min is None) and (x_max is None):
    x_min = 0
    x_max = 50
  elif x_max is None:
    x_max = x_min
  
  data_xs = np.random.uniform(x_min,x_max,n)
  if std == 0:
      data_ys = data_generating_function(data_xs)  
  else:
      data_ys = np.random.normal(data_generating_function(data_xs), std)
  
  return data_xs, data_ys 

def observe_data(ripl,data_xs,data_ys):
  ripl.set_mode("church_prime")
  ripl.observe("(gp ( array %s ) )" % np.array_str(data_xs)[1:-1],array(data_ys))
  ripl.set_mode("venture_script")

@nottest
def gp_test_skeleton(f, n, std, ripl, test, inference_prog=None, obs_statements=None):
  if obs_statements is None:
    obs_statements  = []

  # iterating through list of forced observations
  for observation in obs_statements:
     ripl.execute_program(observation) 

  if inference_prog is not None:
    ripl.execute_program(inference_prog)
 
  if n > 0: 
    data_xs,data_ys  = generate_synthetic_data(f,n,std)
    observe_data(ripl, data_xs, data_ys)


  
  return test(ripl,f)

def prep_ripl(program, prep_for_structure_learning=False):
  ripl = get_ripl()
  ripl.set_mode("venture_script")
  ripl.assume("zero","gp_mean_const( 0.)")
  if prep_for_structure_learning:

    ripl.bind_foreign_sp("string_concatenate",
	deterministic_typed(lambda x,y: x + y, [t.StringType(),t.StringType()], t.StringType(),
			    descr="Concatenates a string"))
    ripl.bind_foreign_sp("int2str",
      deterministic_typed(str, [t.IntegerType()], t.StringType(),
	descr="Concatenates a string"))

  ripl.execute_program(program)
  
  return ripl

############################################################
#	   Functions for Hypothesis Tests 
#
############################################################
@nottest
def test_global_log_joint_lt0(ripl, _):
  error_message = """
      log score is larger than 0
  """
  print ripl.infer("global_log_joint")
  assert ripl.infer("global_log_joint")[0] < 0, error_message 

@nottest
def test_global_log_joint_smoke(ripl, _):
  error_message = """
      log score is really large: > 1000  
  """
  print ripl.infer("global_log_joint")
  assert ripl.infer("global_log_joint")[0] < 1000, error_message 

def mean_posterior_samples_interpolation(ripl,f_true):
  ripl.assume("gp_out_sample","gp(array(10))",label="pid")
  ripl.set_mode("church_prime")
  post_samples = collectSamples(ripl,"pid")
  xs = [p[0] for p in post_samples ]
  return reportKnownMean(f_true(10), xs)

def ks_posterior_samples_interpolation(ripl,f_true, std=2):
  ripl.assume("gp_out_sample","gp(array(10))",label="pid")
  ripl.set_mode("church_prime")
  post_samples = collectSamples(ripl,"pid",num_samples=100)
  xs = [p[0] for p in post_samples ]
  return reportKnownGaussian(f_true(10), std, xs)

def mean_posterior_samples_extrapolation(ripl,f_true):
  ripl.assume("gp_out_sample","gp(array(60))",label="pid")
  ripl.set_mode("church_prime")
  post_samples = collectSamples(ripl,"pid")
  xs = [p[0] for p in post_samples ]
  return reportKnownMean(f_true(60), xs)

def ks_posterior_samples_extrapolation(ripl,f_true, std=2):
  ripl.assume("gp_out_sample","gp(array(60))",label="pid")
  ripl.set_mode("church_prime")
  post_samples = collectSamples(ripl,"pid",num_samples=100)
  xs = [p[0] for p in post_samples ]
  return reportKnownGaussian(f_true(60), std, xs)
@nottest
def smoke_test(ripl, _):
  error_message = """
    with input array size 2 gp should sample output list of length 2
    """
  assert len(ripl.sample("gp(array(1, 2))")) == 2, error_message
def produce_plots(ripl, f):
  plt.figure()
  n_samples = 100
  x = np.linspace(0, 50, 100)
  plt.plot(x,f(x), sns.xkcd_rgb["denim blue"],zorder=1)
  ripl.set_mode("church_prime")
  for _ in range(n_samples ):
    y = ripl.sample("( gp (array %s ) )" % \
      np.array_str(np.random.uniform(0,50,100))[1:-1])
    plt.plot(x,y,c="red",alpha=0.05,linewidth=2,zorder=2)
  plt.axis([0,50,-10,10])
  plt.savefig("test/inference_quality/micro/result_figures/" +
    str(datetime.datetime.now()) + "posterior_samples.png")

