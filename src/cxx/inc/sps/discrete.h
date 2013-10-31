#ifndef DISCRETE_SPS_H
#define DISCRETE_SPS_H

#include "sp.h"

struct FlipSP : SP
{ 
  FlipSP(std::string s): SP(s) {}
  VentureValue * simulateOutput(Node * node, SPAux * spAux) override; 
};


#endif
