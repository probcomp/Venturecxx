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
#include "sp.h"
#include "sps/bool.h"
#include "value.h"
#include <cassert>
#include <vector>

VentureValue * BoolAndSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureBool * b1 = dynamic_cast<VentureBool *>(operands[0]->getValue());
  VentureBool * b2 = dynamic_cast<VentureBool *>(operands[1]->getValue());
  assert(b1);
  assert(b2);
  return new VentureBool(b1->pred && b2->pred);
}

VentureValue * BoolOrSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureBool * b1 = dynamic_cast<VentureBool *>(operands[0]->getValue());
  VentureBool * b2 = dynamic_cast<VentureBool *>(operands[1]->getValue());
  assert(b1);
  assert(b2);
  return new VentureBool(b1->pred || b2->pred);
}

VentureValue * BoolNotSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
    vector<Node *> & operands = node->operandNodes;
    VentureBool * b = dynamic_cast<VentureBool *>(operands[0]->getValue());
    assert(b);
    return new VentureBool(!b->pred);
}

VentureValue * BoolXorSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureBool * b1 = dynamic_cast<VentureBool *>(operands[0]->getValue());
  VentureBool * b2 = dynamic_cast<VentureBool *>(operands[1]->getValue());
  assert(b1);
  assert(b2);
  return new VentureBool((b1->pred && !b2->pred) || (b2->pred && !b1->pred));
}

