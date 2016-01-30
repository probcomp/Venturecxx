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

#include "sps/conditional.h"
#include "utils.h"
#include "expressions.h"

VentureValuePtr BranchRequestPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("branch", args, 3);

  int expIndex = 2;
  if (args->operandValues[0]->getBool()) { expIndex = 1; }
  VentureValuePtr expression = args->operandValues[expIndex];

  vector<ESR> esrs;
  esrs.push_back(ESR(VentureValuePtr(new VentureID()),quote(expression),args->env));
  return shared_ptr<VentureRequest>(new VentureRequest(esrs, vector<shared_ptr<LSR> >()));
}

VentureValuePtr BiplexOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("if", args, 3);
  if (args->operandValues[0]->getBool()) { return args->operandValues[1]; }
  else { return args->operandValues[2]; }
}
