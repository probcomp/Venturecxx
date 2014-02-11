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
#include "value.h"


#include "sp.h"
#include "sps/vector.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <cassert>
#include <iostream>
#include <typeinfo>

VentureValue * MakeVectorSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<VentureValue *> vec;
  for (Node * operand : node->operandNodes)
  {
    vec.push_back(operand->getValue());
  }
  return new VentureVector(vec);
}

VentureValue * VectorLookupSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureVector * vec = dynamic_cast<VentureVector *>(operands[0]->getValue());
  VentureNumber * i = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(vec);
  assert(i);

  return vec->xs[i->getInt()];
}
