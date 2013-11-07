#ifndef FLOAT_SPS_H
#define FLOAT_SPS_H

#include "sp.h"

/* Deterministic Real SPs. */
struct PlusSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct MinusSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct TimesSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct DivideSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct EqualSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct GreaterThanSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct LessThanSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct GreaterThanOrEqualToSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct LessThanOrEqualToSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct RealSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};


#endif
