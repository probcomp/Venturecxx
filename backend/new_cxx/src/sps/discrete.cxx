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

#include "sps/discrete.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>
#include <boost/foreach.hpp>

#include "utils.h"
#include "numerical_helpers.h"


VentureValuePtr FlipOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("flip", args, 0, 1);
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getProbability(); }
  int n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  return VentureValuePtr(new VentureBool(n));
}

double FlipOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getProbability(); }

  if (value->getBool()) { return log(p); }
  else { return log(1 - p); }
}

vector<VentureValuePtr> FlipOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getProbability(); }

  vector<VentureValuePtr> vs;

  if (p > 0) { vs.push_back(VentureValuePtr(new VentureBool(true))); }
  if (p < 1) { vs.push_back(VentureValuePtr(new VentureBool(false))); }
  return vs;
}

VentureValuePtr BernoulliOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("bernoulli", args, 0, 1);
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getProbability(); }
  int n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  return VentureValuePtr(new VentureInteger(n));
}

double BernoulliOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getProbability(); }

  if (value->getBool()) { return log(p); }
  else { return log(1 - p); }
}

vector<VentureValuePtr> BernoulliOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getProbability(); }

  vector<VentureValuePtr> vs;

  if (p > 0) { vs.push_back(VentureValuePtr(new VentureAtom(1))); }
  if (p < 1) { vs.push_back(VentureValuePtr(new VentureAtom(0))); }
  return vs;
}


VentureValuePtr UniformDiscreteOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("uniform_discrete", args, 2);

  long lower = args->operandValues[0]->getInt();
  long upper = args->operandValues[1]->getInt();

  int n = gsl_rng_uniform_int(rng, upper - lower);
  return VentureValuePtr(new VentureInteger(lower + n));
}

double UniformDiscreteOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  checkArgsLength("uniform_discrete", args, 2);

  long lower = args->operandValues[0]->getInt();
  long upper = args->operandValues[1]->getInt();
  long sample = value->getInt();

  return log(gsl_ran_flat_pdf(sample,lower,upper));
}

vector<VentureValuePtr> UniformDiscreteOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  checkArgsLength("uniform_discrete", args, 2);

  long lower = args->operandValues[0]->getInt();
  long upper = args->operandValues[1]->getInt();

  vector<VentureValuePtr> vs;

  for (long index = lower; index <= upper; index++) // TODO Fencepost error?
  {
    vs.push_back(shared_ptr<VentureValue>(new VentureNumber(index)));
  }
  return vs;
}


VentureValuePtr BinomialOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("binomial", args, 2);
  int n = args->operandValues[0]->getInt();
  double p = args->operandValues[1]->getProbability();
  int val = gsl_ran_binomial(rng,p,n);
  return VentureValuePtr(new VentureNumber(val));
}

double BinomialOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  checkArgsLength("binomial", args, 2);
  int n = args->operandValues[0]->getInt();
  double p = args->operandValues[1]->getProbability();
  int val = value->getInt();
  // TODO: compute probability in logspace
  return log(gsl_ran_binomial_pdf(val,p,n));
}


VentureValuePtr CategoricalOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("categorical", args, 1, 2);
  if (args->operandValues.size() == 1) { return simulateCategorical(args->operandValues[0]->getSimplex(),rng); }
  else { return simulateCategorical(args->operandValues[0]->getSimplex(),args->operandValues[1]->getArray(),rng); }
}
double CategoricalOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  checkArgsLength("categorical", args, 1, 2);
  if (args->operandValues.size() == 1) { return logDensityCategorical(value,args->operandValues[0]->getSimplex()); }
  else { return logDensityCategorical(value,args->operandValues[0]->getSimplex(),args->operandValues[1]->getArray()); }
}

vector<VentureValuePtr> CategoricalOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  const Simplex& s = args->operandValues[0]->getSimplex();

  vector<VentureValuePtr> vs;

  if (args->operandValues.size() == 1)
  {
    for (size_t i = 0; i < s.size(); ++i)
    {
      if (s[i] > 0)
      {
        vs.push_back(VentureValuePtr(new VentureAtom(i)));
      }
    }
  }
  else
  {
    const vector<VentureValuePtr>& os = args->operandValues[1]->getArray();

    for (size_t i = 0; i < s.size(); ++i)
    {
      if (s[i] > 0)
      {
        vs.push_back(os[i]);
      }
    }
  }

  return vs;
}

VentureValuePtr LogCategoricalOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("log_categorical", args, 1, 2);
  vector<double> ps = mapExpUptoMultConstant(args->operandValues[0]->getSimplex());
  size_t sample = sampleCategorical(ps,rng);

  if (args->operandValues.size() == 1) { return VentureValuePtr(new VentureNumber(sample)); }
  else { return args->operandValues[1]->getArray()[sample]; }
}

double LogCategoricalOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  checkArgsLength("log_categorical", args, 1, 2);

  const vector<double> ps = args->operandValues[0]->getSimplex();
  double logscore = 0;

  if (args->operandValues.size() == 1) { logscore = ps[value->getInt()]; }
  else { logscore = ps[findVVPtr(value,args->operandValues[1]->getArray())]; }

  logscore -= logSumExp(ps);
  return logscore;
}

vector<VentureValuePtr> LogCategoricalOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  if (args->operandValues.size() == 1)
  {
    const Simplex& s = args->operandValues[0]->getSimplex();

    vector<VentureValuePtr> vs;
    for (size_t i = 0; i < s.size(); ++i)
      { vs.push_back(VentureValuePtr(new VentureAtom(i))); }
    return vs;
  }
  else
  {
    return args->operandValues[1]->getArray();
  }
}

VentureValuePtr SymmetricDirichletOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("symmetric_dirichlet", args, 2);
  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();
  vector<double> alphaVector(n,alpha);
  Simplex theta(n,-1);

  gsl_ran_dirichlet(rng,static_cast<uint32_t>(n),&alphaVector[0],&theta[0]);
  return VentureValuePtr(new VentureSimplex(theta));;
}

double SymmetricDirichletOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  checkArgsLength("symmetric_dirichlet", args, 2);
  double alpha = args->operandValues[0]->getDouble();
  int n = args->operandValues[1]->getInt();
  vector<double> alphaVector(n,alpha);
  /* TODO GC watch the NEW */
  Simplex theta = value->getSimplex();
  return gsl_ran_dirichlet_lnpdf(static_cast<uint32_t>(n),&alphaVector[0],&theta[0]);
}

VentureValuePtr DirichletOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("dirichlet", args, 1);
  vector<VentureValuePtr> vs = args->operandValues[0]->getArray();
  vector<double> xs;
  BOOST_FOREACH(VentureValuePtr v , vs) { xs.push_back(v->getDouble()); }
  Simplex theta(xs.size(),-1);
  gsl_ran_dirichlet(rng,xs.size(),&xs[0],&theta[0]);
  return VentureValuePtr(new VentureSimplex(theta));;
}

double DirichletOutputPSP::logDensity(VentureValuePtr value,shared_ptr<Args> args) const
{
  checkArgsLength("dirichlet", args, 1);
  vector<VentureValuePtr> vs = args->operandValues[0]->getArray();
  vector<double> xs;
  BOOST_FOREACH(VentureValuePtr v , vs) { xs.push_back(v->getDouble()); }
  Simplex theta = value->getSimplex();
  return gsl_ran_dirichlet_lnpdf(xs.size(),&xs[0],&theta[0]);
}

/* Poisson */
VentureValuePtr PoissonOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  return VentureValuePtr(new VentureInteger(gsl_ran_poisson(rng,args->operandValues[0]->getDouble())));
}

double PoissonOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  return PoissonDistributionLogLikelihood(value->getInt(),args->operandValues[0]->getDouble());
}
