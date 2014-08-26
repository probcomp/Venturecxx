import numpy as np
from venture.lite.builtin import deterministic_typed
import venture.lite.value as v

def loadUtilSPs(ripl):
  utilSPsList = [
      [ "linear_logistic", deterministic_typed(lambda w,x: 1/(1+np.exp(-(w[0] + np.dot(w[1:], x)))),
          [v.HomogeneousArrayType(v.NumberType()), v.HomogeneousArrayType(v.NumberType())], v.NumberType(),
          descr="linear_logistic(w, x) returns the output of logistic regression with weight and input") ]]

  for name,sp in dict(utilSPsList).iteritems():
    ripl.bind_foreign_sp(name, sp)
