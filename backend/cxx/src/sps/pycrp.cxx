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
#include "sps/pycrp.h"
#include "value.h"
#include "node.h"
#include "utils.h"
#include <cassert>

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf_gamma.h>


VentureValue * MakePitmanYorCRPSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  assert(alpha);
  double d = 0.0;
  if (operands.size() > 1)
  {
    VentureNumber * vd = dynamic_cast<VentureNumber *>(operands[1]->getValue());
    assert(vd);
    d = vd->x;
  }
  return new VentureSP(new PitmanYorCRPSP(alpha->x,d));
}

VentureValue * PitmanYorCRPSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  PitmanYorCRPSPAux * aux = dynamic_cast<PitmanYorCRPSPAux*>(node->spaux());
  assert(aux);

  vector<uint32_t> tables;  
  vector<double> counts;

  for (pair<uint32_t,uint32_t> p : aux->tableCounts)
  {
    tables.push_back(p.first);
    counts.push_back(p.second - d);
  }
  tables.push_back(aux->nextIndex);
  counts.push_back(alpha + aux->numTables * d);

  normalizeVector(counts);

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < counts.size(); ++i)
  {
    sum += counts[i];
    if (u < sum) { return new VentureAtom(tables[i]); }
  }
  assert(false);
  return nullptr;
}

double PitmanYorCRPSP::logDensityOutput(VentureValue * value, Node * node) const
{
  PitmanYorCRPSPAux * aux = dynamic_cast<PitmanYorCRPSPAux*>(node->spaux());
  VentureAtom * table = dynamic_cast<VentureAtom*>(value);
  assert(aux);
  assert(table);

  if (aux->tableCounts.count(table->n))
  { return log(aux->tableCounts[table->n] - d) - log(aux->numCustomers + alpha); }
  else
  { return log(alpha + aux->numTables * d) - log(aux->numCustomers + alpha); }
}

void PitmanYorCRPSP::incorporateOutput(VentureValue * value, Node * node) const
{
  PitmanYorCRPSPAux * aux = dynamic_cast<PitmanYorCRPSPAux*>(node->spaux());
  VentureAtom * table = dynamic_cast<VentureAtom*>(value);
  assert(aux);
  assert(table);

  aux->numCustomers++;
  if (aux->tableCounts.count(table->n))
  { 
    aux->tableCounts[table->n]++; 
  }
  else
  {
    aux->tableCounts[table->n] = 1;
    aux->numTables++;
    aux->nextIndex++;
  }
}

void PitmanYorCRPSP::removeOutput(VentureValue * value, Node * node) const
{
  PitmanYorCRPSPAux * aux = dynamic_cast<PitmanYorCRPSPAux*>(node->spaux());
  VentureAtom * table = dynamic_cast<VentureAtom*>(value);
  assert(aux);
  assert(table);

  aux->numCustomers--;
  aux->tableCounts[table->n]--;
  if (aux->tableCounts[table->n] == 0)
  {
    aux->numTables--;
    aux->tableCounts.erase(table->n);
  }
}

double PitmanYorCRPSP::logDensityOfCounts(SPAux * spaux) const
{
  PitmanYorCRPSPAux * aux = dynamic_cast<PitmanYorCRPSPAux*>(spaux);
  assert(aux);

  double sum = gsl_sf_lngamma(alpha) - gsl_sf_lngamma(alpha + aux->numCustomers);
  size_t k = 0;
  for (pair<uint32_t,uint32_t> p : aux->tableCounts)
  {
    sum += gsl_sf_lngamma(p.second - d);
    sum += log(alpha + k * d);
    k++;
  }
  return sum;
}
