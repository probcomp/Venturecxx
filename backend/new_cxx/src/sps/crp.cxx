// Copyright (c) 2013, 2014 MIT Probabilistic Computing Project.
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

#include "sps/crp.h"
#include "value.h"
#include "args.h"
#include "sp.h"
#include "sprecord.h"
#include "node.h"
#include "utils.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf_gamma.h>

#include <boost/foreach.hpp>

// TODO needed for BOOST_FOREACH macro
// (cannot use a type with a comma)
typedef pair<uint32_t,uint32_t> tableCountPair;

boost::python::object CRPSPAux::toPython(Trace * trace) const
{
  return toPythonDict(trace, tableCounts);
}

// Maker
VentureValuePtr MakeCRPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("make_crp", args, 1, 2);
  
  double alpha = args->operandValues[0]->getDouble();
  double d = 0;
  
  if (args->operandValues.size() == 2) { d = args->operandValues[1]->getDouble(); }

  return VentureValuePtr(new VentureSPRecord(new CRPSP(alpha, d),new CRPSPAux()));
}

// Made

CRPSP::CRPSP(double alpha, double d) : SP(new NullRequestPSP(), new CRPOutputPSP(alpha, d)), alpha(alpha), d(d) {}

boost::python::dict CRPSP::toPython(Trace * trace, shared_ptr<SPAux> spAux) const
{
  boost::python::dict crp;
  crp["type"] = "crp";
  crp["alpha"] = alpha;
  crp["d"] = d;
  crp["counts"] = spAux->toPython(trace);
  
  boost::python::dict value;
  value["type"] = "sp";
  value["value"] = crp;
  
  return value;
}

VentureValuePtr CRPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("crp", args, 0);  
  
  shared_ptr<CRPSPAux> aux = dynamic_pointer_cast<CRPSPAux>(args->spAux);
  assert(aux);

  vector<uint32_t> tables;  
  vector<double> counts;

  BOOST_FOREACH(tableCountPair p, aux->tableCounts)
  {
    tables.push_back(p.first);
    counts.push_back(p.second - d);
  }
  tables.push_back(aux->nextIndex);
  counts.push_back(alpha + aux->numTables * d);

  Simplex ps = normalizeVector(counts);

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < counts.size(); ++i)
  {
    sum += ps[i];
    if (u < sum) { return VentureValuePtr(new VentureAtom(tables[i])); }
  }
  assert(false);
  return VentureValuePtr();
}


double CRPOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<CRPSPAux> aux = dynamic_pointer_cast<CRPSPAux>(args->spAux);
  assert(aux);
  uint32_t table = value->getInt();

  if (aux->tableCounts.count(table))
  { return log(aux->tableCounts[table] - d) - log(aux->numCustomers + alpha); }
  else
  { return log(alpha + aux->numTables * d) - log(aux->numCustomers + alpha); }
}

void CRPOutputPSP::incorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<CRPSPAux> aux = dynamic_pointer_cast<CRPSPAux>(args->spAux);
  assert(aux);
  uint32_t table = value->getInt();

  aux->numCustomers++;
  if (aux->tableCounts.count(table))
  { 
    aux->tableCounts[table]++; 
  }
  else
  {
    aux->tableCounts[table] = 1;
    aux->numTables++;
    aux->nextIndex = std::max(aux->nextIndex, table + 1);
  }
}

void CRPOutputPSP::unincorporate(VentureValuePtr value,shared_ptr<Args> args) const
{
  shared_ptr<CRPSPAux> aux = dynamic_pointer_cast<CRPSPAux>(args->spAux);
  assert(aux);
  uint32_t table = value->getInt();

  aux->numCustomers--;
  aux->tableCounts[table]--;
  if (aux->tableCounts[table] == 0)
  {
    aux->numTables--;
    aux->tableCounts.erase(table);
  }
  // TODO Consider decrementing the nextIndex while the top table is
  // empty, or even maintaining a free list.  Why?  So that
  // resimulating big blocks of CRPs produces the same atoms.  Does
  // this actually matter?  If the atoms are memoized on?
}

double CRPOutputPSP::logDensityOfCounts(shared_ptr<SPAux> spAux) const
{
  shared_ptr<CRPSPAux> aux = dynamic_pointer_cast<CRPSPAux>(spAux);
  assert(aux);

  double sum = gsl_sf_lngamma(alpha) - gsl_sf_lngamma(alpha + aux->numCustomers);
  size_t k = 0;

  BOOST_FOREACH (tableCountPair p, aux->tableCounts)
  {
    sum += gsl_sf_lngamma(p.second - d);
    sum += log(alpha + k * d);
    k++;
  }
  return sum;
}

vector<VentureValuePtr> CRPOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  shared_ptr<CRPSPAux> aux = dynamic_pointer_cast<CRPSPAux>(args->spAux);
  vector<VentureValuePtr> vs;

  BOOST_FOREACH (tableCountPair p, aux->tableCounts) {
    vs.push_back(VentureValuePtr(new VentureAtom(p.first)));
  }
  vs.push_back(VentureValuePtr(new VentureAtom(aux->nextIndex)));
  
  return vs;
}

