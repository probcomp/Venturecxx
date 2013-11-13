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
#include "sps/makeucsymdirmult.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>


VentureValue * MakeUCSymDirMultSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * n = dynamic_cast<VentureNumber *>(operands[1]->getValue());

  assert(alpha);
  assert(n);

  uint32_t d = static_cast<uint32_t>(n->x);

  double *alphaVector = new double[d];
  for (size_t i = 0; i < d; ++i) 
  { 
    alphaVector[i] = alpha->x;
  }

  /* TODO GC watch the NEW */
  double *theta = new double[d];

  gsl_ran_dirichlet(rng,d,alphaVector,theta);

  delete[] alphaVector;
  return new VentureSP(new UCSymDirMultSP(theta,d));
}

double MakeUCSymDirMultSP::logDensityOutput(VentureValue * value, Node * node) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * n = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureSP * vsp = dynamic_cast<VentureSP *>(value);
  assert(alpha);
  assert(n);
  assert(vsp);

  uint32_t d = static_cast<uint32_t>(n->x);

  double *alphaVector = new double[d];
  for (size_t i = 0; i < d; ++i) { alphaVector[i] = alpha->x; }

  UCSymDirMultSP * sp = dynamic_cast<UCSymDirMultSP *>(vsp->sp);

  double ld = gsl_ran_dirichlet_lnpdf(d,alphaVector,sp->theta);
  delete[] alphaVector;
  return ld;
}

VentureValue * MakeUCSymDirMultAAAKernel::simulate(VentureValue * oldVal, Node * appNode, LatentDB * latentDB, gsl_rng * rng)
{

  vector<Node *> & operands = appNode->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * n = dynamic_cast<VentureNumber *>(operands[1]->getValue());

  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(appNode->madeSPAux);

  assert(alpha);
  assert(n);
  assert(spaux);

  uint32_t d = static_cast<uint32_t>(n->x);

  double *conjAlphaVector = new double[d];
  for (size_t i = 0; i < d; ++i) 
  { 
    conjAlphaVector[i] = alpha->x + spaux->counts[i];
  }

  /* TODO GC watch the NEW */
  double *theta = new double[d];

  gsl_ran_dirichlet(rng,d,conjAlphaVector,theta);

  delete[] conjAlphaVector;
  return new VentureSP(new UCSymDirMultSP(theta,d));
}

double MakeUCSymDirMultAAAKernel::weight(VentureValue * newVal, VentureValue * oldVal, Node * appNode, LatentDB * latentDB)
{
  return 0;
}

double UCSymDirMultSP::logDensityOfCounts(SPAux * generic_spaux) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(generic_spaux);
  assert(spaux);

  return gsl_ran_multinomial_lnpdf(n,theta,&(spaux->counts[0]));
}

VentureValue * UCSymDirMultSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < n; ++i)
  {
    sum += theta[i];
    if (u < sum) { return new VentureAtom(i); }
  }
  assert(false);
  return nullptr;
}  


double UCSymDirMultSP::logDensityOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;

  return theta[observedIndex];
}

void UCSymDirMultSP::incorporateOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]++;
}

void UCSymDirMultSP::removeOutput(VentureValue * value, Node * node) const
{
  SymDirMultSPAux * spaux = dynamic_cast<SymDirMultSPAux *>(node->spaux());
  assert(spaux);

  VentureAtom * vint = dynamic_cast<VentureAtom*>(value);
  assert(vint);
  uint32_t observedIndex = vint->n;
  spaux->counts[observedIndex]--;
}

SPAux * UCSymDirMultSP::constructSPAux() const
{
  return new SymDirMultSPAux(n);
}

void UCSymDirMultSP::destroySPAux(SPAux *spaux) const
{
  delete spaux;
}



