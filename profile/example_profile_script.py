from venture.shortcuts import *
import cProfile

def RIPL():
  return make_church_prime_ripl()

def loadTrickCoin():
  ripl = RIPL()
  ripl.assume("coin_is_tricky","(bernoulli 0.1)",label="istricky")
  ripl.assume("weight","(if coin_is_tricky (beta 1.0 1.0) 0.5)")
  ripl.observe("(bernoulli weight)","true")

  return ripl


def profileReferencesProgram(N):
  ripl = loadTrickCoin()
  cProfile.runctx("ripl.infer(%d)" % N,None,locals(),"profile_trickycoin.pyprof")

profileReferencesProgram(1000)

