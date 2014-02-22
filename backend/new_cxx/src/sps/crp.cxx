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

// Maker
VentureValuePtr MakeCRPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  double alpha = args->operandValues[0]->getDouble();
  double d = 0;

  if (args->operandValues.size() > 1) { d = args->operandValues[1]->getDouble(); }

  PSP * requestPSP = new NullRequestPSP();
  PSP * outputPSP = new CRPOutputPSP(alpha, d);
  return VentureValuePtr(new VentureSPRecord(new SP(requestPSP,outputPSP),new CRPSPAux()));
}

// Made

VentureValuePtr CRPOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
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
    aux->nextIndex++;
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


