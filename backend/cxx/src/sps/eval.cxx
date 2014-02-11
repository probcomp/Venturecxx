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
#include "sps/eval.h"
#include "env.h"
#include "value.h"
#include "node.h"
#include "srs.h"
#include "all.h"
#include <vector>

VentureValue * EvalSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  size_t id = reinterpret_cast<size_t>(node);


  vector<Node *> & operands = node->operandNodes;
  VentureEnvironment * env = dynamic_cast<VentureEnvironment*>(operands[1]->getValue());
  assert(env);
  return new VentureRequest({ESR(id,operands[0]->getValue(),env)});
}
