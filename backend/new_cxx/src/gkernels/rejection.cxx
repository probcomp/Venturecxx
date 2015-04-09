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

#include "gkernels/rejection.h"
#include "concrete_trace.h"
#include "scaffold.h"
#include "db.h"
#include "regen.h"
#include "detach.h"
#include "consistency.h"

pair<Trace*,double> BogoPossibilizeGKernel::propose(ConcreteTrace * trace,shared_ptr<Scaffold> scaffold)
{
  this->trace = trace;
  this->scaffold = scaffold;
  
  assert(scaffold->border.size() == 1);
  while (true) {
    pair<double,shared_ptr<DB> > p = detachAndExtract(trace,scaffold->border[0],scaffold);
    double rhoWeight = p.first;
    rhoDB = p.second;

    assertTorus(scaffold);

    double xiWeight = regenAndAttach(trace,scaffold->border[0],scaffold,false,rhoDB,shared_ptr<map<Node*,Gradient> >());
    cout << rhoWeight << ", " << xiWeight << endl;
    if (rhoWeight > -INFINITY) {
      // The original state was possible; force rejecting the transition
      return make_pair(trace, -INFINITY);
    } else if (xiWeight > -INFINITY) {
      // Moving from impossible to possible state; force accepting the
      // transition
      return make_pair(trace, INFINITY);
    } else {
      this->reject(); // To restore everything to its proper state TODO use particles?
    }
  }
}

void BogoPossibilizeGKernel::accept() { }


void BogoPossibilizeGKernel::reject()
{
  detachAndExtract(trace,scaffold->border[0],scaffold);
  assertTorus(scaffold);
  regenAndAttach(trace,scaffold->border[0],scaffold,true,rhoDB,shared_ptr<map<Node*,Gradient> >());
}
