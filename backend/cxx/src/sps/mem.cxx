#include "value.h"
#include "node.h"
#include "sp.h"
#include "spaux.h"
#include "env.h"
#include "sps/mem.h"
#include "utils.h"

#include <boost/functional/hash.hpp>
#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;

VentureValue * MSPMakerSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
/* TODO GC share somewhere here? */
  return new VentureSP(new MSP(operands[0]));
}

size_t MSP::hashValues(vector<Node *> operands) const
{
  size_t seed = 0;
  for (Node * operand : operands) { seed += operand->getValue()->toHash(); }
  return seed;
}

VentureValue * MSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  uint32_t id = hashValues(operands);

  VentureEnvironment * env = new VentureEnvironment;
  env->addBinding(new VentureSymbol("memoizedSP"), sharedOperatorNode);

  VentureList * exp = new VentureNil;

  node->spaux()->familyValues.insert({id, vector<VentureValue*> {}});

  /* TODO URGENT the creator is priviledged! Massive error. */
  for (Node * operand : reverse(operands))
  {
    VentureValue * val = operand->getValue()->clone();
    /* Give ownership over the cloned value to the family */
    node->spaux()->familyValues[id].push_back(val);
    exp = new VenturePair(val,exp);
  }
  exp = new VenturePair(new VentureSymbol("memoizedSP"),exp);
  return new VentureRequest({ESR(id,exp,env)});
}

void MSP::flushRequest(VentureValue * value) const
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
