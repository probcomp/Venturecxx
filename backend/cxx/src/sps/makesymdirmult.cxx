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
#include "sps/makesymdirmult.h"
#include "gsl/gsl_sf_gamma.h"

#include<boost/range/numeric.hpp>

VentureValue * MakeSymDirMultSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * n = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(alpha);
  assert(n);
  return new VentureSP(new SymDirMultSP(alpha->x,static_cast<uint32_t>(n->x)));
}

VentureValue * MakeSymDirMultRegSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * n = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(alpha);
  assert(n);
  return new VentureSP(new SymDirMultSP(alpha->x,static_cast<uint32_t>(n->x)));
}

double SymDirMultSP::logDensityOfCounts(SPAux * generic_spaux) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(generic_spaux);
  assert(spaux);

  auto N = boost::accumulate(spaux->counts, 0);
  double A = alpha * spaux->counts.size();

  double x = gsl_sf_lngamma(A) - gsl_sf_lngamma(N + A);
  for (auto count : spaux->counts)
  {
    x += gsl_sf_lngamma(alpha + count) - gsl_sf_lngamma(alpha);
  }
  return x;
}

VentureValue * SymDirMultSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  vector<double> xs;
  for (auto x : spaux->counts)
  {
    xs.push_back(x + alpha);
  }
  normalizeVector(xs);
  return new VentureAtom(sampleCategorical(xs,rng));
}

double SymDirMultSP::logDensityOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;

  vector<double> xs;
  for (auto x : spaux->counts)
  {
    xs.push_back(x + alpha);
  }
  normalizeVector(xs);
  return log(xs[observedIndex]);
}

void SymDirMultSP::incorporateOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]++;
}

void SymDirMultSP::removeOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]--;
}

SPAux * SymDirMultSP::constructSPAux() const
{
  return new SymDirMultSPAux(n);
}

void SymDirMultSP::destroySPAux(SPAux *spaux) const
{
  delete spaux;
}
