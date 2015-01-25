import sys

import venture.shortcuts as s
from model import build_brownian_model

def main():
  step = float(sys.argv[1])
  noise = float(sys.argv[2])
  r = s.Puma().make_church_prime_ripl()
  r.execute_program(build_brownian_model(step, noise))
  for i in range(8):
    print i, r.sample("(obs_fun %s)" % i)

if __name__ == "__main__":
  main()
