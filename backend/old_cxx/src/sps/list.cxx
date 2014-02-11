/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
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

    VentureValue * val = new VenturePair(new VentureSymbol("quote"),
					 new VenturePair(pair->first,
							 new VentureNil));
    assert(val);
 
    /* TODO this may be problematic */
    size_t id = reinterpret_cast<size_t>(node) + i;

    VenturePair * exp = new VenturePair(new VentureSymbol("mappedSP"),
					new VenturePair(val,
							new VentureNil));


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
      delete exp->first;
      VenturePair * quote = dynamic_cast<VenturePair*>(exp->rest);
      assert(quote);
      delete quote->first;
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







