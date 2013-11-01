#ifndef CSP_SP_H
#define CSP_SP_H

#include "address.h"
#include "exp.h"
#include "sp.h"
#include <vector>
#include <string>

struct CSP : SP
{
  /* TODO GC major GC issue with values. Right now the values in the expression
     will be shared by all applications of the csp! */
  CSP(const Address & a, const std::vector<std::string> ids, Expression & body, const Address & envAddr): 
    SP(a), ids(ids), body(body), envAddr(envAddr) 
    { isCSRReference = true; }

  VentureValue * simulateRequest(Node * node, gsl_rng * rng) override;

  Address addr;
  std::vector<std::string> ids; 
  Expression body;
  Address envAddr;
};




#endif
