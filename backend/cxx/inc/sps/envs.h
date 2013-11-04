#ifndef ENV_SPS_H
#define ENV_SPS_H

#include "sp.h"

struct GetCurrentEnvSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  void flushOutput(VentureValue * value) const override; 
};

struct GetEmptyEnvSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct ExtendEnvSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};


#endif
