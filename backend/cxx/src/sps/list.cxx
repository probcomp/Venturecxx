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

  size_t i = 0;
  while (!dynamic_cast<VentureNil*>(list))
  {
    VenturePair * pair = dynamic_cast<VenturePair*>(list);
    assert(pair);
 
    VenturePair * exp = new VenturePair(new VentureSymbol("mappedSP"),
					new VenturePair(pair->first->clone()->inverseEvaluate(),
							new VentureNil));
    /* TODO this may be problematic */
    size_t id = reinterpret_cast<size_t>(node) + i;

    esrs.push_back(ESR(id,exp,env));
    i++;
    list = pair->rest;
  }
  return new VentureRequest(esrs);
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
      VentureList * list = exp;
      while (!dynamic_cast<VentureNil*>(list))
      {
	VenturePair * pair = dynamic_cast<VenturePair*>(list);
	assert(pair);
	delete pair->first;
	list = pair->rest;
      }
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







