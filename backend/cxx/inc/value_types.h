#ifndef VALUE_TYPES_H
#define VALUE_TYPES_H

#include "value.h"
#include "exp.h"
#include "env.h"
#include "spaux.h"
#include "srs.h"

#include <vector>
struct SP;

/* Returned by QUOTE. */
struct VentureExpression : VentureValue 
{ 
  VentureExpression(Expression * exp): exp(exp) {}
  Expression * exp; 
};

struct VentureEnvironment : VentureValue 
{ 
  VentureEnvironment(Environment env): env(env) {}
  Environment env;
};

/* RequestPSPs must return VentureRequests. */
struct VentureRequest : VentureValue
{
  VentureRequest() {}
  VentureRequest(std::vector<CSR> csrs): csrs(csrs) {}
  VentureRequest(std::vector<ESR *> esrs): esrs(esrs) {}
  
  std::vector<CSR> csrs;
  std::vector<ESR *> esrs;
};

/* TODO SP or PSP?
   (just for serializing/deserializing?) 
   called for: destruction, serializing, deserializing
 */
struct VentureTokenValue : VentureValue 
{ 
  VentureTokenValue(SP * owner): owner(owner) {}
  SP * owner;
};

/* TODO unique_ptrs or shared_ptrs or "last" ptrs */
struct VentureSPValue : VentureTokenValue 
{ 
  VentureSPValue(SP * sp): VentureTokenValue(nullptr), sp(sp) {}

  VentureSPValue(SP * owner,SP * sp, SPAux * spAux):
    VentureTokenValue(owner), sp(sp), spAux(spAux) {}

  SP * sp;
  SPAux * spAux;
};


#endif


