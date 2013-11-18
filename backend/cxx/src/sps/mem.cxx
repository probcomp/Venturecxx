#include "value.h"
#include "node.h"
#include "sp.h"
#include "spaux.h"
#include "env.h"
#include "sps/mem.h"
#include "utils.h"

#include <iostream>


#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;

VentureValue * MSPMakerSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
/* TODO GC share somewhere here? */
  return new VentureSP(new MSP(args.operands[0]));
}


VentureValue * MSP::simulateRequest(const Args & args, gsl_rng * rng) const
{
  MSPAux * aux = dynamic_cast<MSPAux*>(node->spaux());
  assert(aux);

  VentureValue * args = new VentureVector(args.operands);

  if (aux->ids.count(args))
  {
    ESR esr(aux->ids[args].first,nullptr,nullptr);
    deepDelete(args);
    return new VentureRequest({esr});
  }

  deepDelete(args);

  // Note: right now this isn't incremented until incorporateRequest,
  // so races may be possible in some contexts that we do not currently
  // support.
  size_t id = aux->nextID;

  assert(!node->spaux()->ownedValues.count(id));

  VentureEnvironment * env = new VentureEnvironment;
  env->addBinding(new VentureSymbol("memoizedSP"), sharedOperatorNode);

  VentureList * exp = new VentureNil;

  for (Node * operand : reverse(args.operands))
  {
    VentureValue * clone = operand->clone();
    VentureSymbol * quote = new VentureSymbol("quote");
    VentureNil * nil = new VentureNil;
    VenturePair * innerPair = new VenturePair(clone,nil);
    VentureValue * val = new VenturePair(quote,innerPair);
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

void MSP::incorporateRequest(VentureValue * value, const Args & args) const
{
  MSPAux * aux = dynamic_cast<MSPAux*>(node->spaux());
  assert(aux);

  VentureRequest * requests = dynamic_cast<VentureRequest*>(value);
  assert(requests);

  assert(requests->esrs.size() == 1);
  ESR esr = requests->esrs[0];

  VentureValue * args = new VentureVector(args.operands);

  if (aux->ids.count(args))
  {
    assert(aux->ids[args].first == esr.id);
    assert(aux->ids[args].second > 0);
    aux->ids[args].second++;
    deepDelete(args);
  }
  else
  {
    aux->nextID++;
    aux->ids.insert(make_pair(args, make_pair(esr.id,1)));
  }
}


void MSP::removeRequest(VentureValue * value, const Args & args) const
{
  MSPAux * aux = dynamic_cast<MSPAux*>(node->spaux());
  assert(aux);

  VentureRequest * requests = dynamic_cast<VentureRequest*>(value);
  assert(requests);

  assert(requests->esrs.size() == 1);
  ESR esr = requests->esrs[0];

  VentureValue * args = new VentureVector(args.operands);

  assert(aux->ids.count(args));
  assert(aux->ids[args].first == esr.id);
  assert(aux->ids[args].second > 0);
  aux->ids[args].second--;

  if (aux->ids[args].second == 0)
  {
    auto originalArgs = aux->ids.find(args);
    assert(originalArgs != aux->ids.end());
    VentureValue * oldArgs = originalArgs->first;
    aux->ids.erase(args);
    deepDelete(oldArgs);
  }
  deepDelete(args);
}


SPAux * MSP::constructSPAux() const { return new MSPAux; }
void MSP::destroySPAux(SPAux * spaux) const { delete spaux; }

MSPAux::~MSPAux()
{
  vector<VentureValue *> args;
  for (pair<VentureValue*,pair<size_t,uint32_t> > pp : ids)
  {
    args.push_back(pp.first);
  }
  for (VentureValue * val : args)
  {
    deepDelete(val);
  }
}

