#ifndef CSP_SP_H
#define CSP_SP_H

#include "sp.h"
#include <vector>
#include <string>

struct MakeCSP : SP
{
  VentureValue * simulateOutput(Node * node, gsl_rng * rng) const override;
};

struct CSP : SP
{
  /* TODO GC major GC issue with values. Right now the values in the expression
     will be shared by all applications of the csp! */
  CSP(VentureValue * ids, VentureValue * body, VentureEnvironment * env): 
    ids(dynamic_cast<VentureList*>(ids)), body(body), env(env)
    { 
      assert(ids);
      isESRReference = true;
      makesESRs = true;
    }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) const override;
  void flushRequest(VentureValue * value) const override;

  VentureList * ids;
  VentureValue * body;
  VentureEnvironment * env;
};




#endif
