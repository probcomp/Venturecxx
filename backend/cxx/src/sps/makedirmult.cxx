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
#include "sps/makedirmult.h"
#include "gsl/gsl_sf_gamma.h"

#include<boost/range/numeric.hpp>

VentureValue * MakeDirMultSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<double> alphaVector;
  for (Node * operandNode : node->operandNodes)
  {
    VentureNumber * alpha_i = dynamic_cast<VentureNumber *>(operandNode->getValue());
    assert(alpha_i);
    alphaVector.push_back(alpha_i->x);
  }

  return new VentureSP(new DirMultSP(alphaVector));
}

double DirMultSP::logDensityOfCounts(SPAux * generic_spaux) const
{
  DirMultSPAux * spaux = dynamic_cast<DirMultSPAux *>(generic_spaux);
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

VentureValue * DirMultSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  DirMultSPAux * spaux = dynamic_cast<DirMultSPAux *>(node->spaux());
  assert(spaux);

  vector<double> xs;
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    xs.push_back(alphaVector[i] + spaux->counts[i]);
  }
  normalizeVector(xs);
  return new VentureAtom(sampleCategorical(xs,rng));
}

double DirMultSP::logDensityOutput(VentureValue * value, Node * node) const
{
  DirMultSPAux * spaux = dynamic_cast<DirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;

  vector<double> xs;
  for (size_t i = 0; i < alphaVector.size(); ++i)
  {
    xs.push_back(alphaVector[i] + spaux->counts[i]);
  }
  normalizeVector(xs);
  return log(xs[observedIndex]);
}

void DirMultSP::incorporateOutput(VentureValue * value, Node * node) const
{
  DirMultSPAux * spaux = dynamic_cast<DirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]++;
}

void DirMultSP::removeOutput(VentureValue * value, Node * node) const
{
  DirMultSPAux * spaux = dynamic_cast<DirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]--;
}

SPAux * DirMultSP::constructSPAux() const
{
  return new DirMultSPAux(alphaVector.size());
}

void DirMultSP::destroySPAux(SPAux *spaux) const
{
  delete spaux;
}
