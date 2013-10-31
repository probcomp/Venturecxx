#ifndef CONTINUOUS_SPS_H
#define CONTINUOUS_SPS_H

#include "sp.h"

/* Continuous scalar random SPs. */
struct NormalSP : SP
{ 
  NormalSP(std::string s): SP(s) { isRandomOutput = true; }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
  double logDensityOutput(VentureValue * value, Node * node) override; 
};

struct GammaSP : SP
{ 
  GammaSP(std::string s): SP(s) { isRandomOutput = true; }
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
  double logDensityOutput(VentureValue * value, Node * node) override; 
};


#endif
