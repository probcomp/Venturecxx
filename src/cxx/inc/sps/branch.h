#ifndef BRANCH_SP_H
#define BRANCH_SP_H

#include "address.h"
#include "exp.h"
#include "sp.h"
#include <vector>
#include <string>

struct BiplexSP : SP
{
  BiplexSP(const Address & a): SP(a) { isCSRReference = true; }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) override;

};




#endif
