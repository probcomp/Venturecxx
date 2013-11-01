#include "node.h"
#include "spaux.h"
#include "value.h"


#include "sps/csp.h"
#include <string>
#include <vector>

#include <boost/functional/hash.hpp>

VentureValue * CSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  /* TODO awkward, maybe buggy */
  size_t id = reinterpret_cast<size_t>(node);
  Environment extendEnv(envNode);
  for (size_t i = 0; i < ids.size(); ++i)
    {
      extendEnv.addBinding(ids[i],node->operandNodes[i]);
    }
  return new VentureRequest({ESR(id,body,extendEnv)});
}

void CSP::destroyValuesInExp(Expression & exp)
{
  if (exp.value) { delete exp.value; }
  for (Expression e : exp.exps) { destroyValuesInExp(e); }
}

CSP::~CSP()
{
  if (ownsExp) { destroyValuesInExp(body); }
}
