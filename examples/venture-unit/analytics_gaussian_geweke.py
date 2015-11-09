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

from venture.unit import *
from venture.venturemagics.ip_parallel import *
import time
# class GaussianModel(VentureUnit):
#     def makeAssumes(self):
#       self.assume('mu', '(tag (quote params) 0 (normal 0 10))')
#       self.assume('sigma', '(tag (quote params) 1 (sqrt (inv_gamma 1 1)))')
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
  [ASSUME mu (tag (quote parameters) 0 (normal 0 10))]
  [ASSUME sigma (tag (quote parameters) 1 (gamma 1 1) ) ]
  [ASSUME x (tag (quote data) 0 (lambda () (normal mu sigma)))]
  '''
###


infer_statement = '(mh default one 20)' #infer_scope = '(mh params all 10)'
hmc = '(hmc default one .05 10 1)'

# mu has high variance prior, sigma has low variance prior.
# if x is close to mu, hard to change value of x.
fail_assumes = [ ('mu', '(tag (quote params) 0 (normal 0 30))') ,
            ('sigma', '(tag (quote params) 1 (gamma .1 1))'),
            ('x', '(lambda () (normal mu sigma))') ]

# variances are better matched and '(mh default one)' should move
# around prior well
pass_assumes = [ ('mu', '(tag (quote params) 0 (normal 0 1))') ,
            ('sigma', '(tag (quote params) 1 (gamma 1 1))'),
            ('x', '(lambda () (normal mu sigma))') ]
hmc_assumes = [ ('mu', '(tag (quote params) 0 (normal 0 1))') ]

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
