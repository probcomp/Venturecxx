#ifndef VECTOR_SP_H
#define VECTOR_SP_H




#include "sp.h"

#include <vector>
#include <string>

struct MakeVectorSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct VectorLookupSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override { }
};




#endif
