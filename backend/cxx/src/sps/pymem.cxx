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
#include "sps/pymem.h"
#include "value.h"
#include "env.h"
#include "node.h"
#include "utils.h"
#include <cassert>

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf_gamma.h>

#include <boost/range/adaptor/reversed.hpp>

using boost::adaptors::reverse;

VentureValue * MakePYMemSP::simulateOutput(Node * node, gsl_rng * rng) const
{
  vector<Node *> & operands = node->operandNodes;

  Node * sharedOperatorNode = operands[0];

  VentureNumber * alpha = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(alpha);

  double d = 0.0;
  if (operands.size() > 2)
  {
    VentureNumber * vd = dynamic_cast<VentureNumber *>(operands[2]->getValue());
    assert(vd);
    d = vd->x;
  }

  return new VentureSP(new PYMemSP(sharedOperatorNode,alpha->x,d));
}

VentureValue * PYMemSP::simulateRequest(Node * node, gsl_rng * rng) const
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
  size_t id = counts.size();
  for (size_t i = 0; i < counts.size(); ++i)
  {
    sum += counts[i];
    if (u < sum) { id = i; break; }
  }
  assert(id < counts.size());

  if (aux->families.count(id))
  {
    ESR esr(id,nullptr,nullptr);
    return new VentureRequest({esr});
  }

  VentureEnvironment * env = new VentureEnvironment;
  env->addBinding(new VentureSymbol("pymemoizedSP"), sharedOperatorNode);

  VentureList * exp = new VentureNil;

  for (Node * operand : reverse(node->operandNodes))
  {
    VentureValue * clone = operand->getValue()->clone();
    VentureSymbol * quote = new VentureSymbol("quote");
    VentureNil * nil = new VentureNil;
    VenturePair * innerPair = new VenturePair(clone,nil);
    VentureValue * val = new VenturePair(quote,innerPair);

    exp = new VenturePair(val,exp);
  }
  exp = new VenturePair(new VentureSymbol("pymemoizedSP"),exp);
  return new VentureRequest({ESR(id,exp,env)});
}

double PYMemSP::logDensityRequest(VentureValue * value, Node * node) const
{
  PitmanYorCRPSPAux * aux = dynamic_cast<PitmanYorCRPSPAux*>(node->spaux());
  VentureRequest * request = dynamic_cast<VentureRequest*>(value);
  assert(aux);
  assert(request);

  size_t id = request->esrs[0].id;
  if (aux->tableCounts.count(id))
  { return log(aux->tableCounts[id] - d) - log(aux->numCustomers + alpha); }
  else
  { return log(alpha + aux->numTables * d) - log(aux->numCustomers + alpha); }
}

void PYMemSP::incorporateRequest(VentureValue * value, Node * node) const
{
  PitmanYorCRPSPAux * aux = dynamic_cast<PitmanYorCRPSPAux*>(node->spaux());
  VentureRequest * request = dynamic_cast<VentureRequest*>(value);
  assert(aux);
  assert(request);
  size_t id = request->esrs[0].id;

  aux->numCustomers++;
  if (aux->tableCounts.count(id))
  { 
    aux->tableCounts[id]++; 
  }
  else
  {
    aux->tableCounts[id] = 1;
    aux->numTables++;
    aux->nextIndex++;
  }
}

void PYMemSP::removeRequest(VentureValue * value, Node * node) const
{
  PitmanYorCRPSPAux * aux = dynamic_cast<PitmanYorCRPSPAux*>(node->spaux());
  VentureRequest * request = dynamic_cast<VentureRequest*>(value);
  assert(aux);
  assert(request);
  size_t id = request->esrs[0].id;

  aux->numCustomers--;
  aux->tableCounts[id]--;
  if (aux->tableCounts[id] == 0)
  {
    aux->numTables--;
    aux->tableCounts.erase(id);
  }
}

