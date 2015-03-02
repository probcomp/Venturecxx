'''
DISCLAIMER: This code relied on an older version of plotf, and so will no
longer run as written.
'''

from venture.shortcuts import (make_puma_church_prime_ripl,
                               make_lite_church_prime_ripl)
import numpy as np, scipy as sp, pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns
from scipy.stats import norm
from statsmodels.distributions import ECDF
from venture.unit import VentureUnit

NSAMPLE = 1000
BURN = 100
THIN = 100

def build_ripl():
  ripl = make_lite_church_prime_ripl()
  program = '''
  [ASSUME mu (scope_include (quote parameters) 0 (normal 0 10))]
  [ASSUME sigma (scope_include (quote parameters) 1 (sqrt (inv_gamma 1 1)))]
  [ASSUME x (scope_include (quote data) 0 (lambda () (normal mu sigma)))]
  '''
  ripl.execute_program(program)
  return ripl

def format_results_marginal(res):
  res = res[0]['value']
  return pd.DataFrame({key : map(lambda x: x['value'], res[key]) for key in res})

def collect_marginal_conditional(ripl):
  'Take draws from priors for mu and sigma'
  infer_statement = '''
  [INFER
    (let ((ds (empty)))
      (do
        (cycle ((bind (collect mu sigma) (curry into ds))
                (mh (quote parameters) all 1))
          {0})))]'''.format(NSAMPLE)
  res = format_results_marginal(ripl.execute_program(infer_statement))
  return res

def format_results_successive(res):
  out = []
  for item in res:
    tmp = item[-2]['value']
    out.append(pd.Series({x : tmp[x][0]['value'] for x in tmp}))
  return pd.concat(out, axis = 1).T

def collect_succesive_conditional(ripl):
  'Simulate data, infer based on it, forget the simulation, repeat'
  # program = '''
  #   forgetme : [ASSUME dummy (x)]
  #   [INFER (cycle
  #            ((peek mu) (peek sigma) (peek dummy)
  #             (hmc (quote parameters) all 0.05 10 1)) 1)]
  #   [FORGET forgetme]'''
  program = '''
    forgetme : [ASSUME dummy (x)]
    [INFER (cycle
             ((peek mu) (peek sigma) (peek dummy)
              (mh (quote parameters) one 1)) 1)]
    [FORGET forgetme]'''
  # program = '''
  #   forgetme : [ASSUME dummy (x)]
  #   [INFER (cycle
  #            ((peek mu) (peek sigma) (peek dummy)
  #             (slice (quote params) 0 10 100 1)
  #             (slice (quote params) 1 1 100 1)) 1)]
  #   [FORGET forgetme]'''
  res = []
  for i in range(BURN + NSAMPLE * THIN):
    tmp = ripl.execute_program(program)
    if (i >= BURN) and not ((i - BURN) % THIN):
      res.append(tmp)
      print (i - BURN) / THIN
  return format_results_successive(res)

def compute_statistics(df, g):
  'Compute the 2 first and 3 second moments of the parameter vector (mu, sigma)'
  res = pd.DataFrame([f(df) for f in g]).T
  res.columns = ['g' + str(i + 1) for i in range(res.shape[1])]
  M = res.shape[0]
  # TODO: the estimate of sigma2_g may be biased for df_successive because the
  # samples are correlated. look into that before implementing the general version
  g_bar, sigma2_g = res.mean(), res.var()
  return {'g' : res, 'M' : M, 'g_bar' : g_bar, 'sigma2_g' : sigma2_g}

def hypothesis_tests(stats_marginal, stats_successive):
  n = len(stats_marginal['g_bar'])
  ix = stats_marginal['g'].columns
  stats = []
  ps = []
  for i in range(n):
    # the test statistic
    stat = ((stats_marginal['g_bar'][i] - stats_successive['g_bar'][i]) /
            np.sqrt(stats_marginal['sigma2_g'][i] / stats_marginal['M'] +
                    stats_successive['sigma2_g'][i] / stats_successive['M']))
    # the p value
    p = min(norm.cdf(stat), 1 - norm.cdf(stat)) * 2
    stats.append(stat); ps.append(p)
  return (pd.Series(stats, index = ix, name = 'test_statistics'),
          pd.Series(ps, index = ix, name = 'p_values'))

def one_pp_plot(g_marginal, g_successive, ax, p):
  thismin = min(g_marginal.min(), g_successive.min())
  thismax = max(g_marginal.max(), g_successive.max())
  t = np.linspace(thismin,thismax, 1000)
  ecdf_marginal = ECDF(g_marginal)
  ecdf_successive = ECDF(g_successive)
  ax.plot(ecdf_marginal(t), ecdf_successive(t), lw = 2)
  ax.plot([0,1], [0,1], '--', lw = 2)
  ax.set_xlim([-0.05,1.05])
  ax.set_ylim([-0.05,1.05])
  ax.set_xlabel('Marginal')
  ax.set_ylabel('Successive')
  ax.text(x = 0, y = 1, s = 'p value: {0:0.2f}'.format(p),
          verticalalignment = 'top')

def pp_plots(stats_marginal, stats_successive, stats, ps, out = None):
  n = len(stats)
  fig, ax = plt.subplots(n, 1, figsize = [6, n * 4])
  for i in range(n):
    one_pp_plot(stats_marginal['g'].iloc[:,i],
                stats_successive['g'].iloc[:,i],
                ax[i], ps[i])
  if out is None: out = 'geweke-results/mh-one-report.pdf'
  fig.savefig(out, format = 'pdf')

def parameter_histograms(df_marginal, df_successive):
  fig, ax = plt.subplots(2, 1, figsize = [6,10])
  for i, param in enumerate(['mu', 'sigma']):
    sns.distplot(df_marginal[param], label = 'marginal', ax = ax[i])
    sns.distplot(df_successive[param], label = 'conditional', ax = ax[i])
    ax[i].set_title(param)
  fig.savefig('geweke-results/mh-one-parameters.pdf')

def main():
  df_marginal = collect_marginal_conditional(build_ripl())
  df_successive = collect_succesive_conditional(build_ripl())
  parameter_histograms(df_marginal, df_successive)
  # the list of functions of the data and parameters to compute
  g = [lambda df: df.mu,
       lambda df: df.sigma,
       lambda df: df.mu ** 2,
       lambda df: df.sigma ** 2,
       lambda df: df.mu * df.sigma]
  stats_marginal = compute_statistics(df_marginal, g)
  stats_successive = compute_statistics(df_successive, g)
  stats, ps = hypothesis_tests(stats_marginal, stats_successive)
  pp_plots(stats_marginal, stats_successive, stats, ps)

def analytics_comparison():
  '''
  Run Geweke test using Analytics framework
  '''
  class GaussianModel(VentureUnit):
    def makeAssumes(self):
      self.assume('mu', '(scope_include (quote params) 0 (normal 0 10))')
      self.assume('sigma', '(scope_include (quote params) 1 (sqrt (inv_gamma 1 1)))')
      self.assume('x', '(lambda () (normal mu sigma))')

    def makeObserves(self):
      self.observe('(x)', 1.0)

  ripl = make_lite_church_prime_ripl()
  model = GaussianModel(ripl).getAnalytics(ripl)
  fh, ih, cr = model.gewekeTest(samples = 100000,
                                infer = '(hmc default all 0.05 10 1)',
                                plot = True)
  with open('geweke-results/analytics-hmc.txt', 'w') as f:
    f.write(cr.reportString)
  cr.compareFig.savefig('geweke-results/analytics-hmc.pdf', format = 'pdf')

if __name__ == '__main__':
  # main()
  # run the comparison
  analytics_comparison()






