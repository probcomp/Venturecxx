#ifndef FLOAT_SPS_H
#define FLOAT_SPS_H

#include "sp.h"

/* Deterministic Float SPs. */
struct FloatPlusSP : SP
{ 
  FloatPlusSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
};

struct FloatTimesSP : SP
{ 
  FloatTimesSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
};

struct FloatDivideSP : SP
{ 
  FloatDivideSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override;
};

struct FloatEqualSP : SP
{ 
  FloatEqualSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
};

struct FloatGreaterThanSP : SP
{
  FloatGreaterThanSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override;
};

struct FloatLessThanSP : SP
{ 
  FloatLessThanSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) override; 
};


#endif
