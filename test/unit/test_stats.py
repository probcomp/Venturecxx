from venture.test.stats import *
from scipy import stats

@statisticalTest
def testTwoSampleKS():
  data1 = stats.norm.rvs(size=100, loc=0., scale=1)
  data2 = stats.norm.rvs(size=100, loc=0., scale=1)
  return reportSameContinuous("KS sanity check", data1, data2)

def testTwoSampleChi2():
  data1 = range(5) * 5
  data2 = sorted(data1)
  assert reportSameDiscrete("foo", data1, data2).pval == 1
