#ifndef BOOL_SPS_H
#define BOOL_SPS_H

#include "sp.h"

/* Deterministic Bool SPs. */
struct BoolAndSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct BoolOrSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct BoolNotSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct BoolXorSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

#endif
