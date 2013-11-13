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
#include "infer/mh.h"
#include "node.h"
#include "check.h"
#include "flush.h"
#include "debug.h"
#include "trace.h"
#include "scaffold.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>


#include <algorithm>
#include <iostream>

/* ScaffoldMHGKernel */

ScaffoldMHGKernel::ScaffoldMHGKernel(Trace * trace): 
  GKernel(trace), check(trace) {}

void ScaffoldMHGKernel::destroyParameters() { delete scaffold; }
void ScaffoldMHGKernel::loadParameters(MixMHParam * param)
{
  ScaffoldMHParam * sparam = dynamic_cast<ScaffoldMHParam*>(param);
  assert(sparam);
  scaffold = sparam->scaffold;
  delete sparam;
}


double ScaffoldMHGKernel::propose()
{
  assert(scaffold);
  assert(!rhoDB);

  pair<double, OmegaDB*> rhoInfo = trace->detach(scaffold->border,scaffold);

  double detachWeight = rhoInfo.first;
  rhoDB = rhoInfo.second;

  check.checkTorus(scaffold);
  double regenWeight = trace->regen(scaffold->border,scaffold,false,rhoDB,nullptr);
  return regenWeight - detachWeight;
}

void ScaffoldMHGKernel::accept()
{
  flushDB(rhoDB,false);
  rhoDB = nullptr;
}


void ScaffoldMHGKernel::reject()
{
  pair<double, OmegaDB *> xiInfo = trace->detach(scaffold->border,scaffold);
  OmegaDB * xiDB = xiInfo.second;
  check.checkTorus(scaffold);
  trace->regen(scaffold->border,scaffold,true,rhoDB,nullptr);
  flushDB(rhoDB,true);
  flushDB(xiDB,false);
  rhoDB = nullptr;

}


/* Outermost MixMH */

MixMHIndex * OutermostMixMH::sampleIndex()
{
  uint32_t index = gsl_rng_uniform_int(trace->rng, trace->numRandomChoices());
  Node * pNode = trace->getRandomChoiceByIndex(index);
  return new RCIndex(pNode);
}

double OutermostMixMH::logDensityOfIndex(MixMHIndex * index)
{
  return -log(trace->numRandomChoices());
}
 
MixMHParam * OutermostMixMH::processIndex(MixMHIndex * index)
{
  Node * pNode = dynamic_cast<RCIndex *>(index)->pNode;

  /* Deleted by deepest gkernel's destroyParameters() */
  Scaffold * scaffold = new Scaffold({pNode});

  /* May expose latent bugs */
  if (gsl_ran_flat(trace->rng,0.0,1.0) < 0.5) { reverse(scaffold->border.begin(),scaffold->border.end()); }

  delete index;

  return new ScaffoldMHParam(scaffold,pNode);
}


MixMHIndex * GlobalScaffoldMixMH::sampleIndex() { return nullptr; }
double GlobalScaffoldMixMH::logDensityOfIndex(MixMHIndex * index) { return 0; }
MixMHParam * GlobalScaffoldMixMH::processIndex(MixMHIndex * index) 
{ 
  vector<Node *> rcs = trace->getRandomChoices();
  set<Node *> allNodes(rcs.begin(),rcs.end());
  return new ScaffoldMHParam(new Scaffold(allNodes),nullptr);
};
