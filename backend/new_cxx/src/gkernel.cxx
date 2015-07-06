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

#include "gkernel.h"
#include "detach.h"
#include "utils.h"
#include "particle.h"
#include "consistency.h"
#include "regen.h"
#include "db.h"
#include "trace.h"
#include "args.h"
#include "lkernel.h"
#include <math.h>
#include <boost/foreach.hpp>

void registerDeterministicLKernels(Trace * trace,
  boost::shared_ptr<Scaffold> scaffold,
  const vector<ApplicationNode*>& applicationNodes,
  const vector<VentureValuePtr>& values)
{
  for (size_t i = 0; i < applicationNodes.size(); ++i)
  {
    trace->registerLKernel(scaffold,applicationNodes[i],boost::shared_ptr<DeterministicLKernel>(new DeterministicLKernel(values[i], trace->getPSP(applicationNodes[i]))));
  }
}

