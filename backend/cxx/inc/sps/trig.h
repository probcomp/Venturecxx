#ifndef TRIG_SPS_H
#define TRIG_SPS_H

#include "sp.h"


struct SinSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

struct CosSP : SP
{ 
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override; 
};

#endif
