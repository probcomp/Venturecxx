#ifndef BOOL_SPS_H
#define BOOL_SPS_H

#include "sp.h"

/* Deterministic Bool SPs. */
struct BoolAndSP : SP
{ 
  BoolAndSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
};

struct BoolOrSP : SP
{ 
  BoolOrSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
};

struct BoolNotSP : SP
{ 
  BoolNotSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override;
};

struct BoolXorSP : SP
{ 
  BoolXorSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
};

#endif
