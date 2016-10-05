from nose import SkipTest
from testconfig import config

from venture.test.config import get_ripl
from venture.test.config import collectSamples
from venture.test.stats import statisticalTest, reportKnownDiscrete

def testTrickCoin():
  yield checkTrickCoin, 0, 0.5
  yield checkTrickCoin, 5, 0.5183 # (1/7 + 99/64) / (1/6 + 99/32)
  yield checkTrickCoin, 10, 0.7019 # (1/12 + 99/2048) / (1/11 + 99/1024)
  yield checkTrickCoin, 20, 0.9536 # (1/22 + 99/2**21) / (1/21 + 99/2**20)

@statisticalTest
def checkTrickCoin(n, p, seed):
  if config['get_ripl'] != 'mite':
    raise SkipTest("dpmem only exists in mite")

  ripl = get_ripl(seed=seed)
  ripl.assume("f", "(make_trick_coin 0.99 1000 1)")
  for _ in range(n):
    ripl.observe("(f)", "true")
  ripl.predict("(f)", label="pid")

  predictions = collectSamples(ripl, "pid")
  ans = [(False, 1 - p), (True, p)]
  return reportKnownDiscrete(ans, predictions)
