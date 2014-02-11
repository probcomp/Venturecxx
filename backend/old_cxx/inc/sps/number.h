#ifndef NUMBER_SPS_H
#define NUMBER_SPS_H

#include "sp.h"

/* Deterministic Real SPs. */
struct PlusSP : SP
{ 
  PlusSP(): SP("+") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct MinusSP : SP
{ 
  MinusSP(): SP("-") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct TimesSP : SP
{ 
  TimesSP(): SP("*") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct DivideSP : SP
{ 
  DivideSP(): SP("/") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct PowerSP : SP
{ 
  PowerSP(): SP("pow") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct EqualSP : SP
{ 
  EqualSP(): SP("=") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct GreaterThanSP : SP
{
  GreaterThanSP(): SP(">") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct LessThanSP : SP
{ 
  LessThanSP(): SP("<") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct GreaterThanOrEqualToSP : SP
{
  GreaterThanOrEqualToSP(): SP(">=") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct LessThanOrEqualToSP : SP
{ 
  LessThanOrEqualToSP(): SP("<=") {}
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct RealSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct IntPlusSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct IntMinusSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct IntTimesSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct IntDivideSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct IntEqualSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct AtomEqualSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

#endif
