from scipy import stats

from venture.test.config import in_backend
from venture.test.stats import statisticalTest, reportSameContinuous, reportSameDiscrete

@in_backend("none")
@statisticalTest
def testTwoSampleKS():
  data1 = stats.norm.rvs(size=100, loc=0., scale=1)
  data2 = stats.norm.rvs(size=100, loc=0., scale=1)
  return reportSameContinuous(data1, data2)

@in_backend("none")
def testTwoSampleChi2():
  data1 = range(5) * 5
  data2 = sorted(data1)
  assert reportSameDiscrete(data1, data2).pval == 1
