// Copyright (c) 2014, 2015 MIT Probabilistic Computing Project.
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

#include "psp.h"
#include "values.h"
#include "args.h"
#include "concrete_trace.h"
#include "node.h"
#include "lkernel.h"

#include <iostream>

using std::cout;
using std::endl;

boost::shared_ptr<LKernel> const PSP::getAAALKernel() { return boost::shared_ptr<LKernel>(new DeterministicMakerAAALKernel(this)); }

VentureValuePtr NullRequestPSP::simulate(boost::shared_ptr<Args> args,gsl_rng * rng) const
{
  return boost::shared_ptr<VentureRequest>(new VentureRequest(vector<ESR>(),vector<boost::shared_ptr<LSR> >()));
}


VentureValuePtr ESRRefOutputPSP::simulate(boost::shared_ptr<Args> args,gsl_rng * rng) const
{
//  cout << "ESRRefOutputPSP::simulate(" << args->node << ")" << endl;
  assert(args->esrParentNodes.size() == 1);
  return args->esrParentValues[0];
}

bool ESRRefOutputPSP::canAbsorb(ConcreteTrace * trace,ApplicationNode * appNode,Node * parentNode) const
{
  vector<RootOfFamily> esrParents = trace->getESRParents(appNode);
  assert(esrParents.size() == 1);
  if (parentNode == esrParents[0].get()) { return false; }
  OutputNode * outputNode = dynamic_cast<OutputNode*>(appNode);
  if (outputNode && parentNode == outputNode->requestNode) { return false; }
  return true;
}
