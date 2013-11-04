#ifndef CONTINUOUS_SPS_H
#define CONTINUOUS_SPS_H

#include "sp.h"

/* Continuous scalar random SPs. */
struct NormalSP : SP
{ 
  NormalSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 
};

struct GammaSP : SP
{ 
  GammaSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
    }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 
};

struct UniformContinuousSP : SP
{ 
  UniformContinuousSP()
    { 
      isRandomOutput = true;
      canAbsorbOutput = true;
    }

  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
  double logDensityOutput(VentureValue * value, Node * node) const override; 
};

#endif
