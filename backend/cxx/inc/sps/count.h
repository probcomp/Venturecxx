#ifndef COUNT_SPS_H
#define COUNT_SPS_H

#include "sp.h"

/* Deterministic Count SPs. */
struct CountPlusSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct CountMinusSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct CountTimesSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct CountDivideSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct CountEqualSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct CountGreaterThanSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct CountLessThanSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};


#endif
