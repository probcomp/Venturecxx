#include "node.h"
#include "spaux.h"
#include "value.h"
#include "env.h"
#include "utils.h"
#include "sps/csp.h"
#include <string>
#include <vector>

#include <boost/functional/hash.hpp>

VentureValue * MakeCSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  VentureList * ids = dynamic_cast<VentureList*>(node->operandNodes[0]->getValue());
  VentureValue * body = dynamic_cast<VentureValue*>(node->operandNodes[1]->getValue());
  assert(ids);
  assert(body);
  return new VentureSP(new CSP(ids,body,node->familyEnv));
}


VentureValue * CSP::simulateRequest(const Args & args, gsl_rng * rng) const
{
  /* TODO awkward, maybe buggy */
  size_t id = reinterpret_cast<size_t>(node);
  VentureEnvironment * extendedEnv = new VentureEnvironment(env);

  assert(node->operandNodes.size() >= listLength(ids));
  for (size_t i = 0; i < listLength(ids); ++i)
    {
      extendedEnv->addBinding(dynamic_cast<VentureSymbol*>(listRef(ids,i)),node->operandNodes[i]);
    }
  return new VentureRequest({ESR(id,body,extendedEnv)});
}

void CSP::flushRequest(VentureValue * value) const
{
  VentureRequest * requests = dynamic_cast<VentureRequest*>(value);
  assert(requests);
  delete requests->esrs[0].env;
  delete value;
}
