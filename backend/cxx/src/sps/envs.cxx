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
#include "sps/envs.h"
#include "value.h"
#include "env.h"
#include "node.h"
#include "utils.h"

VentureValue * GetCurrentEnvSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  return node->familyEnv;
}

void GetCurrentEnvSP::flushOutput(VentureValue * value) const { }


VentureValue * GetEmptyEnvSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  return new VentureEnvironment;
}

VentureValue * ExtendEnvSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  VentureEnvironment * env = dynamic_cast<VentureEnvironment*>(node->operandNodes[0]->getValue());
  
  VentureEnvironment * extendedEnv = new VentureEnvironment(env);
  VentureSymbol * vsym = dynamic_cast<VentureSymbol*>(node->operandNodes[1]->getValue());
  assert(vsym);
  extendedEnv->addBinding(vsym,node->operandNodes[2]);
  return extendedEnv;
}

