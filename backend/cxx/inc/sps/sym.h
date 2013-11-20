#ifndef SYMBOL_SPS_H
#define SYMBOL_SPS_H

#include "sp.h"

struct IsSymbolSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

#endif
