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

#include "gkernels/hmc.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "db.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"

pair<Trace*,double> HMCGKernel::propose(ConcreteTrace * trace,boost::shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;
  /* detach and extract */
  pair<double,boost::shared_ptr<DB> > p = detachAndExtract(trace,scaffold->border[0],scaffold);
  double rhoWeight = p.first;
  rhoDB = p.second;
  assertTorus(scaffold);

  

  
  double xiWeight = regenAndAttach(trace,scaffold->border[0],scaffold,false,rhoDB,boost::shared_ptr<map<Node*,Gradient> >());

  return make_pair(trace,xiWeight - rhoWeight);
}

void HMCGKernel::accept() { }


void HMCGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,boost::shared_ptr<map<Node*,Gradient> >());
}
