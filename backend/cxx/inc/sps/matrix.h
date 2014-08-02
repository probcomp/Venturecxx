#ifndef MATRIX_SP_H
#define MATRIX_SP_H




#include "sp.h"

#include <vector>
#include <string>

struct MakeMatrixSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct MatrixLookupSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
  void flushOutput(VentureValue * value) const override { }
};


#endif
