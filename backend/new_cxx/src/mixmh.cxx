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

#include "concrete_trace.h"
#include "scaffold.h"
#include "indexer.h"
#include "gkernel.h"
#include "mixmh.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <cmath>

#include <iostream>
using std::cout;
using std::endl;
using std::flush;

void mixMH(ConcreteTrace * trace,
	   shared_ptr<ScaffoldIndexer> indexer,
	   shared_ptr<GKernel> gKernel)
{
  shared_ptr<Scaffold> index = indexer->sampleIndex(trace);


  double rhoMix = indexer->logDensityOfIndex(trace,index);

  pair<Trace*,double> p = gKernel->propose(trace,index);
  double xiMix = indexer->logDensityOfIndex(p.first,index);

  double alpha = xiMix + p.second - rhoMix;
  double logU = log(gsl_ran_flat(trace->getRNG(),0.0,1.0));

  
  if (logU < alpha) {
    // cout << ".";
    gKernel->accept();
  }
  else
  {
    // cout << "!";
    gKernel->reject();
  }

}
