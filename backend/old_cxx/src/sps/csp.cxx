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
#include "env.h"
#include "utils.h"
#include "sps/csp.h"
#include <string>
#include <vector>

#include <boost/functional/hash.hpp>

VentureValue * MakeCSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureList * ids = dynamic_cast<VentureList*>(node->operandNodes[0]->getValue());
  VentureValue * body = dynamic_cast<VentureValue*>(node->operandNodes[1]->getValue());
  assert(ids);
  assert(body);
  return new VentureSP(new CSP(to_string(reinterpret_cast<size_t>(node)),ids,body,node->familyEnv));
}


VentureValue * CSP::simulateRequest(Node * node, gsl_rng * rng) const
{
  /* TODO awkward, maybe buggy */
  size_t id = reinterpret_cast<size_t>(node);
  VentureEnvironment * extendedEnv = new VentureEnvironment(env);

  assert(node->operandNodes.size() >= listLength(ids));
  for (size_t i = 0; i < listLength(ids); ++i)
    {
      extendedEnv->addBinding(dynamic_cast<VentureSymbol*>(listRef(ids,i)),node->operandNodes[i]);
    }
  return new VentureRequest({ESR(id,body,extendedEnv)});
}

void CSP::flushRequest(VentureValue * value) const
{
  VentureRequest * requests = dynamic_cast<VentureRequest*>(value);
  assert(requests);
  delete requests->esrs[0].env;
  delete value;
}
