#include "sps/discrete.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>
#include <boost/foreach.hpp>

#include "utils.h"



VentureValuePtr FlipOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("flip", args, 0, 1);
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }
  int n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  return VentureValuePtr(new VentureBool(n));
}

double FlipOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }

  if (value->getBool()) { return log(p); }
  else { return log(1 - p); }
}

vector<VentureValuePtr> FlipOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }

  vector<VentureValuePtr> vs;

  if (p > 0) { vs.push_back(VentureValuePtr(new VentureBool(true))); }
  if (p < 1) { vs.push_back(VentureValuePtr(new VentureBool(false))); }
  return vs;
}

VentureValuePtr BernoulliOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("bernoulli", args, 0, 1);
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }
  int n = gsl_ran_bernoulli(rng,p);
  assert(n == 0 || n == 1);
  return VentureValuePtr(new VentureAtom(n));
}

double BernoulliOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }

  if (value->getBool()) { return log(p); }
  else { return log(1 - p); }
}

vector<VentureValuePtr> BernoulliOutputPSP::enumerateValues(shared_ptr<Args> args) const
{
  double p = 0.5;
  if (!args->operandValues.empty()) { p = args->operandValues[0]->getDouble(); }

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
  return VentureValuePtr(new VentureAtom(lower + n));
}

double UniformDiscreteOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  checkArgsLength("uniform_discrete", args, 2);
  
  long lower = args->operandValues[0]->getInt();
  long upper = args->operandValues[1]->getInt();
  long sample = value->getInt();
  
  return log(gsl_ran_flat_pdf(sample,lower,upper));
}

VentureValuePtr BinomialOutputPSP::simulate(shared_ptr<Args> args,gsl_rng * rng) const
{
  checkArgsLength("binomial", args, 2);
  int n = args->operandValues[0]->getInt();
  double p = args->operandValues[1]->getDouble();
  int val = gsl_ran_binomial(rng,p,n);
  return VentureValuePtr(new VentureNumber(val));
}

double BinomialOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  checkArgsLength("binomial", args, 2);
  int n = args->operandValues[0]->getInt();
  double p = args->operandValues[1]->getDouble();
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

//LogLikelihoods, from Yura's Utilities.cpp
double PoissonDistributionLogLikelihood(int sampled_value_count, double lambda) {
  //l^k * e^{-l} / k!
  double loglikelihood = sampled_value_count * log(lambda);
  loglikelihood -= gsl_sf_lnfact(sampled_value_count);
  loglikelihood -= lambda;
  return loglikelihood;
}

/* Poisson */
VentureValuePtr PoissonOutputPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  return VentureValuePtr(new VentureNumber(gsl_ran_poisson(rng,args->operandValues[0]->getDouble())));
}

double PoissonOutputPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  return PoissonDistributionLogLikelihood(value->getInt(),args->operandValues[0]->getDouble());
}
