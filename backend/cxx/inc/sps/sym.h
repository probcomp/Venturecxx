#ifndef SYMBOL_SPS_H
#define SYMBOL_SPS_H

#include "sp.h"

struct IsSymbolSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

#endif
