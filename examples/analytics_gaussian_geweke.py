from venture.unit import *
from venture.venturemagics.ip_parallel import *
import time
# class GaussianModel(VentureUnit):
#     def makeAssumes(self):
#       self.assume('mu', '(scope_include (quote params) 0 (normal 0 10))')
#       self.assume('sigma', '(scope_include (quote params) 1 (sqrt (inv_gamma 1 1)))')
#       self.assume('x', '(lambda () (normal mu sigma))')

#     def makeObserves(self):
#       self.observe('(x)', 1.0)

# ripl = make_lite_church_prime_ripl()
# model = GaussianModel(ripl).getAnalytics(ripl)
# fh, ih, cr = model.gewekeTest(samples = 100000,
#                                 infer = '(hmc default all 0.05 10 1)',
#                                 plot = True)
# with open('geweke-results/analytics-hmc.txt', 'w') as f:
#     f.write(cr.reportString)
# cr.compareFig.savefig('geweke-results/analytics-hmc.pdf', format = 'pdf')


## currently fails in Analytics because of problem extracting assumes from ripl
program = '''
  [ASSUME mu (scope_include (quote parameters) 0 (normal 0 10))]
  [ASSUME sigma (scope_include (quote parameters) 1 (gamma 1 1) ) ]
  [ASSUME x (scope_include (quote data) 0 (lambda () (normal mu sigma)))]
  '''
###


infer_statement = '(mh default one 20)' #infer_scope = '(mh params all 10)'
hmc = '(hmc default one .05 10 1)'

# mu has high variance prior, sigma has low variance prior.
# if x is close to mu, hard to change value of x.
fail_assumes = [ ('mu', '(scope_include (quote params) 0 (normal 0 30))') ,
            ('sigma', '(scope_include (quote params) 1 (gamma .1 1))'),
            ('x', '(lambda () (normal mu sigma))') ]

# variances are better matched and '(mh default one)' should move around prior well 
pass_assumes = [ ('mu', '(scope_include (quote params) 0 (normal 0 1))') ,
            ('sigma', '(scope_include (quote params) 1 (gamma 1 1))'),
            ('x', '(lambda () (normal mu sigma))') ]
hmc_assumes = [ ('mu', '(scope_include (quote params) 0 (normal 0 1))') ]

observes = [('(x)','0')]
hmc_observes = [('(normal mu .4)','0')]


# variables are highly correlated and so '(mh default one)' will never accept
fail_assumes_correlated = [('x','(normal 0 10)'),('y','(normal x .0001)') ]
fail_observes_correlated = None


ripl = mk_l_ripl()
ana = Analytics(ripl,assumes=hmc_assumes,observes=hmc_observes)

t = time.time()
fh,ih,cr = ana.gewekeTest(samples=1000,infer=hmc,useMRipl=False,plot=True)
print 'time: ', time.time() - t




# notes on geweke:                

# Geweke 2004:
# Grosse's blogpost recommends using QQ plots to compare the marginal distributions on variables for forward samples vs. samples from MCMC. Doing so gives rich visual information about these distributions. But one has to be careful with the number of samples (and the autocorrelation of the MCMC samples). I added KS tests, histograms and QQ plots to the Geweke test in Analytics. 

# Geweke himself advocates comparing forward and MCMC samples on various functions g of the parameter vector theta. The examples in the paper are mostly first and second moments of components of theta. Forward samples give a standard MC approximation of the expectation of g(theta) over the prior. The MCMC samples are not independent and so the variance of the estimator is higher (and has to be estimated for the given chain). Using the CLT for independent and dependent samples, we can transform these estimates s.t. their difference is ~ N(0,1). We can then use a standard goodness of fit test to N(0,1). 

# How to automate this version in Venture? First, there needs to be an interface where you enter the function g. You could either specify a Venture function or a Python function. Python functions will be simpler in most cases. Some care may need to be taken with numerical issues if the number of MCMC samples is very large. (You would want to use numpy/scipy functions, rather than write code for computing some function of higher moments yourself). 
 
# You first estimate E( g(theta) ), then you compute its variances. These variances depend on the variance of the expectation and so you can only estimate them. So you need enough samples that your estimate is very close whp. (Geweke runs his tests for 10^5 iterations). Finally you implement/borrow some standard test for samples being ~ N(0,1).

# If theta has high dimension it will have lots of second moments. Geweke suggests we test lots of them and use Bonferronni. (Some models may have a very large number of variables, and so running a KS test on all of them is likely to produce failures due to chance. One could just eyeball the KS p-values. But it might be good to use Bonferroni here also). 

# Since the g(theta) statistics just depend on samples of theta, there is an incremental path from the current QQ plot Geweke for marginals and the generalization to arbitrary functions of theta.

# One obvious advantage of Geweke's approach is in dealing with correlated variables. If x and y are highly correlated in the prior, this will show up in the second moments but not in the first.

# Another possible advantage is in speeding up tests with very large numbers of variables. Before looking at QQ plots and KS tests for each marginal, we might compare expectations for some appropriate real-valued function of all of the variables. This involves throwing away lots of information, but I would think it would expose certain bugs. (We could test this). Another approach for models with many variables is to only read off values for some of them. Geweke doesn't use any function like this in his examples. I wonder if there are problems in doing so? 

# Geweke demonstrates the effectiveness of his test by showing that it catches various intentional bugs, e.g. MCMC sampler has beta(2,2) while the forward sampler has beta(1,1). In implementing Geweke for Venture, it might be hard to test on bugs quite like this. But one could write some buggy variant of some of the simpler inference methods. 


# Discussion with David Wadden and VKM on Geweke and Testing:
# There are a few advantages to having a Geweke that can take any Venture program (in the standard batch inference form, with sequence of finite assumes, then observes, then infers). 

# First, for backend testing, developers can easily create additional Geweke tests using models/inference programs they suspect might be problematic. For backend testing, it's preferable that these programs are simple, transparent, and would have low autocorrelation for the specified kernel (so relatively few MCMC samples are needed to do the Geweke). On the other hand, some errors might not be easy to expose without a fair amount of compute time. (These are likely to be errors that aren't caught by users, because they involve subtle deviations from correctness). Geweke gives an example of a fairly simple mixture of two t-distributions. One bug is that the prior assumes Beta(1,1) on the mixture weights, while the posterior uses Beta(2,2). With 2.5*10^5 samples, this bug is only exposed by 12 of the 20 tests Geweke performs, and only 5 tests have p < .005. 

# Second, if the program transform is sufficiently abstract, it should be robust to various changes in Venture's inference language.

# Third, since the inference language now allows non-convergent programs, there is a need for a basic debugging tool for users. (These could be advanced users experimenting with subtle variants of MCMC that should converge but don't due to errors not in the backend but in their inference program).

# Fourth, Geweke gives a picture of how well the MCMC transition operator moves around when conditioned on plausible data (i.e. data from the prior). Good visualization of this process seems potentially useful as a tool for getting early-warning about a transition operator that is liable to get stuck. (I'm still unclear of the usefulness of Geweke here as opposed to the standard MCMC diagnostics. One issue is that Geweke ignores your actual data, which might be bad if your data has low probability on the prior. Another is that 

# An additional thing to keep in mind: apart from the program transformation, the main thing you need for Geweke is tools for comparing distributions. Currently there is a QQ plot, Axch's KS test from test suite (which uses KS from scipy), and plotting histograms on same axis. All these tools for comparing marginals are also needed for basic MCMC diagnostics. The simplest diagnostic for MCMC is just to compare random variables at two points in the Markov chain (where variables are sampled via parallel chains). If the distributions are different then you haven't converged. The QQ plot could be improved (and maybe a PP plot is better?) and should have documentation explaining its semantics.

# Related, vkm sketched an interesting extension of the current observes->predicts program transformation. You annotate variables with potential kernels for inference, e.g. variables that support gradients, or discrete enumeration, etc. Programs in this form can be automatically coupled with a big space of compatible inference programs (i.e. programs that use any of the permissible kernels on the given variable).










