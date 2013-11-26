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

////////////

VentureValue * ExpBranchSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  size_t id = reinterpret_cast<size_t>(node);

  vector<Node *> & operands = node->operandNodes;
  VentureBool * b = dynamic_cast<VentureBool *>(operands[0]->getValue());
  assert(b);

  size_t index = 2;
  if (b->pred) { index = 1; }
  VentureValue * exp = operands[index]->getValue();
  return new VentureRequest({ESR(id,exp,node->familyEnv)});
}


////////////////////

VentureValue * BiplexSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureBool * b = dynamic_cast<VentureBool *>(operands[0]->getValue());
  bool pred;
  if (b) { pred = b->pred; }
  else
  {
    VentureNumber * n = dynamic_cast<VentureNumber *>(operands[0]->getValue());
    assert(n);
    pred = (n->x != 0);
  }
  if (pred) { return operands[1]->getValue(); }
  else { return operands[2]->getValue(); }
}

void BiplexSP::flushOutput(VentureValue * value) const {}
