#include "node.h"
#include "spaux.h"
#include "value.h"
#include "utils.h"
#include "env.h"
#include "sps/cond.h"


#include <cassert>
#include <string>
#include <vector>

#include <boost/functional/hash.hpp>


VentureValue * BranchSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  size_t id = reinterpret_cast<size_t>(node);

  VentureEnvironment * extendedEnv = new VentureEnvironment(node->familyEnv);

  vector<Node *> & operands = node->operandNodes;
  VentureBool * b = dynamic_cast<VentureBool *>(operands[0]->getValue());
  assert(b);

  size_t index = 2;
  if (b->pred) { index = 1; }
  extendedEnv->addBinding(new VentureSymbol("f"),operands[index]);
  VenturePair * exp = new VenturePair(new VentureSymbol("f"),new VentureNil);
  return new VentureRequest({ESR(id,exp,extendedEnv)});
}

void BranchSP::flushRequest(VentureValue * value) const
{
  VentureRequest * requests = dynamic_cast<VentureRequest*>(value);
  assert(requests);
  assert(requests->esrs.size() == 1);
  ESR esr = requests->esrs[0];
  VenturePair * exp = dynamic_cast<VenturePair*>(esr.exp);
  delete exp->first;
  listShallowDestroy(exp);
  esr.env->destroySymbols();
  delete esr.env;
  delete value;
}
