from venture.venturemagics.ip_parallel import *
# at terminal start ipython cluster
# >  ipcluster start --n=2

v=MRipl(20,backend='lite',local_mode=False)

v.assume('x','(binomial 5 .5)')
v.observe('(poisson x)','1.')
