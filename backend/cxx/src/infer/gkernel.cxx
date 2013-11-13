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
#include "infer/gkernel.h"
#include "node.h"
#include <iostream>

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include "trace.h"
#include <cmath>

void GKernel::infer(uint32_t N)
{
  if (trace->numRandomChoices() == 0) {return;}
  
  for (uint32_t i = 0; i < N; ++i)
  {
    double alpha = propose();
    double logU = log(gsl_ran_flat(trace->rng,0.0,1.0));
    if (logU < alpha) { accept(); }
    else { reject(); }
  }
}


double MixMHKernel::propose()
{
  index = sampleIndex();
  double ldRho = logDensityOfIndex(index);
  /* ProcessIndex is responsible for freeing the index. */
  /* LoadParameters is responsible for freeing the param. */
  gKernel->loadParameters(processIndex(index));
  double alpha = gKernel->propose();
  double ldXi = logDensityOfIndex(index);

  return alpha + ldXi - ldRho;
}
 

