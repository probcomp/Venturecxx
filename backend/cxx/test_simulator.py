from venture.shortcuts import *
import sys
import itertools

def RIPL():
  return make_lite_church_prime_ripl()


def testSimulator1(A,B):
  ripl = RIPL()
  ripl.assume("f","(make_simulator (quote sim1))")
  ripl.assume("s0","(f (quote initialize))")
  ripl.predict("(f (quote simulate) s0 (make_vector))")

