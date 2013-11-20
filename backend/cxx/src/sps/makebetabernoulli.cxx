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
#include "value.h"
#include "utils.h"
#include "node.h"
#include "sp.h"
#include "sps/makebetabernoulli.h"
#include "gsl/gsl_sf_gamma.h"

#include<boost/range/numeric.hpp>

VentureValue * MakeBetaBernoulliSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<double> alphaVector;
  for (Node * operandNode : node->operandNodes)
  {
    VentureNumber * alpha_i = dynamic_cast<VentureNumber *>(operandNode->getValue());
    assert(alpha_i);
    alphaVector.push_back(alpha_i->x);
  }
  assert(alphaVector.size() == 2);

  return new VentureSP(new BetaBernoulliSP(alphaVector));
}

double BetaBernoulliSP::logDensityOfCounts(SPAux * generic_spaux) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(generic_spaux);
  assert(spaux);

  auto N = boost::accumulate(spaux->counts, 0);
  double A = boost::accumulate(alphaVector, 0);

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    x += gsl_sf_lngamma(alphaVector[i] + spaux->counts[i]) - gsl_sf_lngamma(alphaVector[i]);
  }
  return x;
}

VentureValue * BetaBernoulliSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(node->spaux());
  assert(spaux);

  vector<double> xs;
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    xs.push_back(alphaVector[i] + spaux->counts[i]);
  }
  normalizeVector(xs);

  uint32_t n = sampleCategorical(xs,rng);
  return new VentureBool(n == 1);
}

double BetaBernoulliSP::logDensityOutput(VentureValue * value, Node * node) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(node->spaux());
  assert(spaux);

  VentureBool * vb = dynamic_cast<VentureBool*>(value);
  assert(vb);
  uint32_t observedIndex = vb->pred ? 1 : 0;

  vector<double> xs;
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    xs.push_back(alphaVector[i] + spaux->counts[i]);
  }
  normalizeVector(xs);
  return log(xs[observedIndex]);
}

void BetaBernoulliSP::incorporateOutput(VentureValue * value, Node * node) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(node->spaux());
  assert(spaux);

  VentureBool * vb = dynamic_cast<VentureBool*>(value);
  assert(vb);
  uint32_t observedIndex = vb->pred ? 1 : 0;

  spaux->counts[observedIndex]++;
}

void BetaBernoulliSP::removeOutput(VentureValue * value, Node * node) const
{
  BetaBernoulliSPAux * spaux = dynamic_cast<BetaBernoulliSPAux *>(node->spaux());
  assert(spaux);

  VentureBool * vb = dynamic_cast<VentureBool*>(value);
  assert(vb);
  uint32_t observedIndex = vb->pred ? 1 : 0;

  spaux->counts[observedIndex]--;
}

SPAux * BetaBernoulliSP::constructSPAux() const
{
  return new BetaBernoulliSPAux(alphaVector.size());
}

void BetaBernoulliSP::destroySPAux(SPAux *spaux) const
{
  delete spaux;
}
