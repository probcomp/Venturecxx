#include "value.h"
#include "node.h"
#include "sp.h"
#include "spaux.h"
#include "env.h"
#include "sps/mem.h"
#include "utils.h"

#include <iostream>

#include <boost/functional/hash.hpp>
#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;

VentureValue * MSPMakerSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
/* TODO GC share somewhere here? */
  return new VentureSP(new MSP(operands[0]));
}

size_t MSP::preprocessHashValue(size_t h) const
{
  h += ~(h << 9);
  h ^=  (h >> 14);
  h +=  (h << 4);
  h ^=  (h >> 10);
  return h;
}


size_t MSP::hashValues(vector<Node *> operands) const
{
  size_t seed = 0;

  for (Node * operand : operands) 
  { 
    boost::hash_combine(seed, preprocessHashValue(operand->getValue()->toHash()));
  }
  return seed;
}

VentureValue * MSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  uint32_t id = hashValues(operands);

  if (node->spaux()->families.count(id)) 
  { 
    return new VentureRequest({ESR(id,nullptr,nullptr)});
  }

  assert(!node->spaux()->ownedValues.count(id));

  VentureEnvironment * env = new VentureEnvironment;
  env->addBinding(new VentureSymbol("memoizedSP"), sharedOperatorNode);

  VentureList * exp = new VentureNil;

  for (Node * operand : reverse(operands))
  {
    VentureValue * val = new VenturePair(new VentureSymbol("quote"),
					 new VenturePair(operand->getValue()->clone(),
							 new VentureNil));

    node->spaux()->ownedValues[id].push_back(val);
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
  if (esr.exp)
  {
    VenturePair * exp = dynamic_cast<VenturePair*>(esr.exp);
    delete exp->first;
    listShallowDestroy(exp);
  }
  if (esr.env)
  {
    esr.env->destroySymbols();
    delete esr.env;
  }

  delete value;
}

