from venture.test.stats import *
from scipy import stats

@statisticalTest
def testTwoSidedKS():
  data1 = stats.norm.rvs(size=100, loc=0., scale=1)
  data2 = stats.norm.rvs(size=100, loc=0., scale=1)
  return reportSameDistribution("KS sanity check", data1, data2)
