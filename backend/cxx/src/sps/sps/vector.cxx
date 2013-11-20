
#include "value.h"


#include "sp.h"
#include "sps/vector.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <cassert>
#include <iostream>
#include <typeinfo>

VentureValue * MakeVectorSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  vector<VentureValue *> vec;
  for (VentureValue * operand : args.operands)
  {
    vec.push_back(operand);
  }
  return new VentureVector(vec);
}

VentureValue * VectorLookupSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureVector * vec = dynamic_cast<VentureVector *>(args.operands[0]);
  VentureNumber * i = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(vec);
  assert(i);

  return vec->xs[i->getInt()];
}
