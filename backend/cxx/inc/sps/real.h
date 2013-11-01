#ifndef FLOAT_SPS_H
#define FLOAT_SPS_H

#include "sp.h"

/* Deterministic Real SPs. */
struct RealPlusSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct RealMinusSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct RealTimesSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct RealDivideSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct RealEqualSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct RealGreaterThanSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct RealLessThanSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};


#endif
