// Copyright (c) 2014 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

#include "sps/scope.h"
#include "node.h"

VentureValuePtr TagOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[2];
}
 
bool TagOutputPSP::canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const
{
  return parentNode != appNode->operandNodes[2];
}

VentureValuePtr ScopeExcludeOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  return args->operandValues[1];
}
 
bool ScopeExcludeOutputPSP::canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const
{
  return parentNode != appNode->operandNodes[1];
}
