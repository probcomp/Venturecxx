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

from venture import shortcuts as s
from venture.exception import underline

ripl = s.make_lite_church_prime_ripl()

ripl.execute_program("""
  [assume tricky (tag (quote tricky) 0 (flip 0.5))]
  [assume weight (if tricky (uniform_continuous 0 1) 0.5)]
  [assume coin (lambda () (flip weight))]
  [observe (coin) true]
  [observe (coin) true]
  [observe (coin) true]
""")

ripl.profiler_enable()
ripl.infer('(mh default one 10)')
ripl.infer('(gibbs tricky one 1)')

def printAddr((did, index)):
  exp = ripl.sivm._get_exp(did)
  text, indyces = ripl.humanReadable(exp, did, index)
  print text
  print underline(indyces)

data = ripl.profile_data()


map(lambda addrs: map(printAddr, addrs), data.principal)

# plot profile data:
# group by principal, operator
# get: mean time, prob accepted, etc.

grouped = data.groupby(['principal', 'operator'], sort=False)

#grouped.alpha.hist(legend=True)
#grouped.alpha.value_counts().plot(kind='hist', legend=True, alpha=0.5)
#import pylab as pl
#pl.show()

