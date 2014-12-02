from venture import shortcuts as s
from venture.exception import underline

ripl = s.make_lite_church_prime_ripl()

ripl.execute_program("""
  [assume tricky (scope_include (quote tricky) 0 (flip 0.5))]
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

