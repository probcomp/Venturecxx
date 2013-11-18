#include "node.h"
#include "sp.h"
#include "sps/discrete.h"
#include "value.h"
#include "utils.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>

#include <iostream>
#include <vector>

//LogLikelihoods, from Yura's Utilities.cpp
double PoissonDistributionLogLikelihood(int sampled_value_count, double lambda) {
  //l^k * e^{-l} / k!
  double loglikelihood = sampled_value_count * log(lambda);
  loglikelihood -= gsl_sf_lnfact(sampled_value_count);
  loglikelihood -= lambda;
  return loglikelihood;
}


/* Bernoulli */

VentureValue * BernoulliSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  double p = 0.5;
  if (!args.operands.empty())
  {
    VentureNumber * vp = dynamic_cast<VentureNumber *>(args.operands[0]);
    assert(vp);
    assert(vp->x >= 0 && vp->x <= 1);
    p = vp->x;
  }
  uint32_t n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  return new VentureBool(n);
} 

double BernoulliSP::logDensityOutput(VentureValue * value, const Args & args) const
{
  VentureBool * b = dynamic_cast<VentureBool *>(value);
  assert(b);

  double p = 0.5;
  if (!args.operands.empty())
  {
    VentureNumber * vp = dynamic_cast<VentureNumber *>(args.operands[0]);
    assert(vp);
    assert(vp->x >= 0 && vp->x <= 1);
    p = vp->x;
  }

  if (b->pred) { return log(p); }
  else { return log(1 - p); }
}

vector<VentureValue*> BernoulliSP::enumerateOutput(const Args & args) const
{
  VentureBool * vold = dynamic_cast<VentureBool*>(node);
  assert(vold);

  double p = 0.5;
  if (!args.operands.empty())
  {
    VentureNumber * vp = dynamic_cast<VentureNumber *>(args.operands[0]);
    assert(vp);
    assert(vp->x >= 0 && vp->x <= 1);
    p = vp->x;
  }

  vector<VentureValue *> vals;
  if (vold->pred && p < 1) { vals.push_back(new VentureBool(false)); }
  else if (!vold->pred && p > 0) { vals.push_back(new VentureBool(true)); }

  return vals;
}

/* Categorical */
VentureValue * CategoricalSP::simulateOutput(const Args & args, gsl_rng * rng) const
{
  vector<double> ps;
  for (Node * operandNode : args.operands)
  {
    VentureNumber * d = dynamic_cast<VentureNumber *>(operandNode);
    assert(d);
    ps.push_back(d->x);
  }
  normalizeVector(ps);

  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < ps.size(); ++i)
  {
    sum += ps[i];
    if (u < sum) { return new VentureAtom(i); }
  }
  assert(false);
} 

double CategoricalSP::logDensityOutput(VentureValue * value, const Args & args) const
{
  VentureAtom * i = dynamic_cast<VentureAtom *>(value);
  assert(i);
  VentureNumber * d = dynamic_cast<VentureNumber *>(args.operands[i->n]);
  assert(d);

  return log(d->x);
}

vector<VentureValue*> CategoricalSP::enumerateOutput(const Args & args) const
{
  VentureAtom * vold = dynamic_cast<VentureAtom*>(node);
  assert(vold);

  vector<VentureValue*> values;

  for (size_t i = 0; i < args.operands.size(); ++i)
  {
    if (i == vold->n) { continue; }
    else {
      VentureNumber * d = dynamic_cast<VentureNumber *>(args.operands[i]);
      assert(d);
      if (d->x > 0) { values.push_back(new VentureAtom(i)); }
    }
  }
  return values;
}

/* UniformDiscrete */
VentureValue * UniformDiscreteSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * a = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * b = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(a);
  assert(b);
  int n = gsl_rng_uniform_int(rng, b->getInt() - a->getInt());
  return new VentureNumber(a->getInt() + n);
}

double UniformDiscreteSP::logDensityOutput(VentureValue * value, const Args & args)  const
{
  VentureNumber * a = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * b = dynamic_cast<VentureNumber *>(args.operands[1]);
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_flat_pdf(x->getInt(),a->getInt(),b->getInt()));
}

vector<VentureValue*> UniformDiscreteSP::enumerateOutput(const Args & args) const
{
  VentureNumber * vold = dynamic_cast<VentureNumber*>(node);
  assert(vold);

  VentureNumber * a = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * b = dynamic_cast<VentureNumber *>(args.operands[1]);
  assert(a);
  assert(b);
  
  vector<VentureValue*> values;

  for (int i = a->getInt(); i < b->getInt(); ++i)
  {
    if (i == vold->getInt()) { continue; }
    else { 
      values.push_back(new VentureNumber(i));
    }
  }
  return values;
}

/* Poisson */
VentureValue * PoissonSP::simulateOutput(const Args & args, gsl_rng * rng)  const
{
  VentureNumber * mu = dynamic_cast<VentureNumber *>(args.operands[0]);
  assert(mu);
  return new VentureNumber(gsl_ran_poisson(rng,mu->x));
}

double PoissonSP::logDensityOutput(VentureValue * value, const Args & args)  const
{
  VentureNumber * mu = dynamic_cast<VentureNumber *>(args.operands[0]);
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(mu);
  assert(x);
  return log(gsl_ran_poisson_pdf(x->getInt(),mu->x));
}
