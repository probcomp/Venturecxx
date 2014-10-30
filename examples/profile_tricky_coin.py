from venture import shortcuts as s
from venture.exception import underline

ripl = s.make_lite_church_prime_ripl()

ripl.execute_program("""
  [assume tricky (flip 0.5)]
  [assume weight (if tricky (uniform_continuous 0 1) 0.5)]
  [assume coin (lambda () (flip weight))]
  [observe (coin) true]
  [observe (coin) true]
  [observe (coin) true]
""")

ripl.profiler_enable()
ripl.infer('(mh default one 100)')

def printAddr((did, index)):
  exp = ripl.sivm._get_exp(did)
  text, indeces = ripl.humanReadable(exp, did, index)
  print text
  print underline(indeces)

map(printAddr, data.principle[0])

