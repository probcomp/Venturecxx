#ifndef BOOL_SPS_H
#define BOOL_SPS_H

#include "sp.h"

/* Deterministic Bool SPs. */
struct BoolAndSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct BoolOrSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

struct BoolNotSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override;
};

struct BoolXorSP : SP
{ 
  VentureValue * simulateOutput(const Args & args, gsl_rng * rng) const override; 
};

#endif
