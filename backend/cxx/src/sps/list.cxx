#include "sps/list.h"
#include "value.h"
#include "node.h"
#include "utils.h"
#include "env.h"
#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;


VentureValue * PairSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureValue * first = operands[0]->getValue();
  VentureList * rest = dynamic_cast<VentureList *>(operands[1]->getValue());
  assert(rest);
  return new VenturePair(first,rest);
}

VentureValue * FirstSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VenturePair * pair = dynamic_cast<VenturePair*>(node->operandNodes[0]->getValue());
  assert(pair);
  return pair->first;
}

VentureValue * RestSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VenturePair * pair = dynamic_cast<VenturePair*>(node->operandNodes[0]->getValue());
  assert(pair);
  return pair->rest;
}

VentureValue * ListSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureList * list = new VentureNil;
  for (Node * operandNode : reverse(node->operandNodes))
  {
    list = new VenturePair(operandNode->getValue(),list);
  }
  return list;
}

void ListSP::flushOutput(VentureValue * value) const 
{
  VentureList * list = dynamic_cast<VentureList*>(value);
  listShallowDestroy(list);
}

VentureValue * IsPairSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  return new VentureBool(dynamic_cast<VenturePair*>(node->operandNodes[0]->getValue()));
}

VentureValue * ListRefSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureList * list = dynamic_cast<VentureList*>(node->operandNodes[0]->getValue());
  VentureNumber * index = dynamic_cast<VentureNumber*>(node->operandNodes[1]->getValue());
  assert(list);
  assert(index);
  return listRef(list,index->getInt());
}


VentureValue * MapListSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  Node * fNode = node->operandNodes[0];
  assert(dynamic_cast<VentureSP*>(fNode->getValue()));

  vector<ESR> esrs;
  VentureList * list = dynamic_cast<VentureList*>(node->operandNodes[1]->getValue());
  assert(list);

  VentureEnvironment * env = new VentureEnvironment;
  env->addBinding(new VentureSymbol("mappedSP"),fNode);

  MapListSPAux * aux = dynamic_cast<MapListSPAux *>(node->spaux());
  assert(aux);

  size_t i = 0;
  while (!dynamic_cast<VentureNil*>(list))
  {
    VenturePair * pair = dynamic_cast<VenturePair*>(list);
    assert(pair);

    VentureValue * val = pair->first->inverseEvaluate();
    assert(val);

 
    /* TODO this may be problematic */
    size_t id = reinterpret_cast<size_t>(node) + i;

    if (dynamic_cast<VentureSymbol*>(pair->first))
    { 
      VenturePair * p = dynamic_cast<VenturePair*>(val);
      assert(p);
      aux->ownedSymbols[id] = p; 
    }
    else if (dynamic_cast<VenturePair*>(pair->first))
    { 
      VenturePair * p = dynamic_cast<VenturePair*>(val);
      assert(p);
      aux->ownedPairs[id] = p; 
    }

    VenturePair * exp = new VenturePair(new VentureSymbol("mappedSP"),
					new VenturePair(val,
							new VentureNil));


    esrs.push_back(ESR(id,exp,env));
    i++;
    list = pair->rest;
  }
  return new VentureRequest(esrs);
}

void MapListSP::flushFamily(SPAux * spaux, size_t id) const
{

  MapListSPAux * aux = dynamic_cast<MapListSPAux *>(spaux);
  assert(aux);


  // VentureSymbol
  if (aux->ownedSymbols.count(id))
  {
    VenturePair * pair = aux->ownedSymbols[id];
    assert(pair);
    delete pair->first;
    listShallowDestroy(pair);
  }
  else if (aux->ownedPairs.count(id))
  {
    VenturePair * pair = aux->ownedPairs[id];
    assert(pair);
    delete pair->first;
    delete pair;
  }
  
}

void MapListSP::flushRequest(VentureValue * value) const
{
  VentureRequest * requests = dynamic_cast<VentureRequest*>(value);
  assert(requests);
  vector<ESR> esrs = requests->esrs;
  if (!esrs.empty())
  {
    esrs[0].env->destroySymbols();
    delete esrs[0].env;

    for (ESR esr : esrs)
    {
      VenturePair * exp = dynamic_cast<VenturePair*>(esr.exp);
      assert(exp);
      delete exp->first;
      listShallowDestroy(exp);
    }
  }
  
  delete value;
}

VentureValue * MapListSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureList * list = new VentureNil;
  for (Node * esrParent : reverse(node->esrParents))
  {
     list = new VenturePair(esrParent->getValue(),list);
  }
  return list;
}

void MapListSP::flushOutput(VentureValue * value) const
{
  VentureList * list = dynamic_cast<VentureList*>(value);
  listShallowDestroy(list);
}







