#include "utils.h"
#include <cmath>

#include "types.h"
#include "values.h"
#include <gsl/gsl_randist.h>

double sumVector(const vector<double> & xs)
{
  double sum = 0;
  for (size_t i = 0; i < xs.size(); ++i) { sum += xs[i]; }
  return sum;
}

Simplex normalizeVector(const vector<double> & xs)
{
  Simplex ps;
  double sum = sumVector(xs);
  double newSum = 0;
  for (size_t i = 0; i < xs.size(); ++i)
  {
    if (sum < 0.000001) { ps.push_back(1.0/xs.size()); }
    else { ps.push_back(xs[i] / sum); }
    newSum += ps[i];
  }
  if (!(fabs(newSum - 1) < 0.01))
  { 
    cout << "sum: " << sum << endl;
    cout << "newSum: " << newSum << endl;
  }
  assert(fabs(newSum - 1) < 0.01);
  return ps;
}


VentureValuePtr simulateCategorical(const Simplex & ps, gsl_rng * rng)
{
  vector<VentureValuePtr> os;
  for (size_t i = 0; i < ps.size(); ++i) { os.push_back(VentureValuePtr(new VentureAtom(i))); }
  return simulateCategorical(ps,os,rng);
}

VentureValuePtr simulateCategorical(const Simplex & xs,const vector<VentureValuePtr> & os, gsl_rng * rng)
{
  Simplex ps = normalizeVector(xs);
  vector<unsigned int> ns(ps.size());
  gsl_ran_multinomial(rng,ps.size(),1,&ps[0],&ns[0]);
  for (size_t i = 0; i < ns.size(); ++i) { if (ns[i] == 1) { return os[i]; } }
  assert(false);
}

double logDensityCategorical(VentureValuePtr val, const Simplex & ps)
{
  vector<VentureValuePtr> os;
  for (size_t i = 0; i < ps.size(); ++i) { os.push_back(VentureValuePtr(new VentureAtom(i))); }
  return logDensityCategorical(val,ps,os);
}

double logDensityCategorical(VentureValuePtr val, const Simplex & xs,const vector<VentureValuePtr> & os)
{
  Simplex ps = normalizeVector(xs);
  for (size_t i = 0; i < os.size(); ++i) { if (os[i]->equals(val)) { return log(ps[i]); } }
  assert(false);
}

