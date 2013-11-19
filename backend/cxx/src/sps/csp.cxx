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
  VentureList * ids = dynamic_cast<VentureList*>(args.operands[0]);
  VentureValue * body = dynamic_cast<VentureValue*>(args.operands[1]);
  assert(ids);
  assert(body);
  return new VentureSP(new CSP(ids,body,args.familyEnv));
}


VentureValue * CSP::simulateRequest(const Args & args, gsl_rng * rng) const
{
  /* TODO awkward, maybe buggy */
  size_t id = reinterpret_cast<size_t>(args.outputNode);
  VentureEnvironment * extendedEnv = new VentureEnvironment(env);

  assert(args.operands.size() >= listLength(ids));
  for (size_t i = 0; i < listLength(ids); ++i)
    {
      extendedEnv->addBinding(dynamic_cast<VentureSymbol*>(listRef(ids,i)),args.operandNodes[i]);
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
