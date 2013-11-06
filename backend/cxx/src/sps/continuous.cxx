#include "node.h"
#include "sp.h"
#include "lkernel.h"
#include "sps/continuous.h"
#include "value.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>

#include <cmath>
#include <vector>

#include <cassert>
#include <iostream>

/* Normal */
VentureValue * NormalSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;

  VentureNumber * vmu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * vsigma = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(vmu);
  assert(vsigma);
  double x = gsl_ran_gaussian(rng, vsigma->x) + vmu->x;
  return new VentureNumber(x);
}

double NormalSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  double mu;
  VentureNumber * vmu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  if (vmu) { mu = vmu->x; }
  else 
  {
    VentureAtom * vcmu = dynamic_cast<VentureAtom*>(operands[0]->getValue());
    assert(vcmu);
    mu = vcmu->n;
  }

  VentureNumber * sigma = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(sigma);
  assert(x);
  return log(gsl_ran_gaussian_pdf(x->x - mu, sigma->x));
}

double NormalSP::logDensityOutputNumeric(double output, const vector<double> & args) const
{
  return log(gsl_ran_gaussian_pdf(output - args[0], args[1]));
}

vector<ParameterScope> NormalSP::getParameterScopes() const
{
  return {ParameterScope::REAL, ParameterScope::POSITIVE_REAL};
}
 
vector<double> NormalSP::gradientOfLogDensity(double output,
					      const vector<double> & arguments) const
{
  double mu = arguments[0];
  double sigma = arguments[1];
  double x = output;

  double gradMu = (x - mu) / (sigma * sigma);
  double gradSigma = (((x - mu) * (x - mu)) - (sigma * sigma)) / (sigma * sigma * sigma);
  return { gradMu, gradSigma };
}

/* Gamma */
VentureValue * GammaSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(a);
  assert(b);
  double x = gsl_ran_gamma(rng, a->x, b->x);
  return new VentureNumber(x);
}

double GammaSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_gamma_pdf(x->x, a->x, b->x));
}


/* UniformContinuous */
VentureValue * UniformContinuousSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(a);
  assert(b);
  double x = gsl_ran_flat(rng,a->x,b->x);
  return new VentureNumber(x);
}

double UniformContinuousSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_flat_pdf(x->x,a->x,b->x));
}

/* Beta */
VentureValue * BetaSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(a);
  assert(b);
  double x = gsl_ran_beta(rng,a->x,b->x);
  return new VentureNumber(x);
}

double BetaSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * a = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * b = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(a);
  assert(b);
  assert(x);
  return log(gsl_ran_beta_pdf(x->x,a->x,b->x));
}


double BetaSP::logDensityOutputNumeric(double output, const vector<double> & args) const
{
  return log(gsl_ran_beta_pdf(output,args[0],args[1]));
}

vector<ParameterScope> BetaSP::getParameterScopes() const
{
  return {ParameterScope::POSITIVE_REAL, ParameterScope::POSITIVE_REAL};
}
 
vector<double> BetaSP::gradientOfLogDensity(double output,
					      const vector<double> & arguments) const
{
  double a = arguments[0];
  double b = arguments[1];

  double alpha0 = a + b;

  double gradA = log(output) + gsl_sf_psi(a) - gsl_sf_psi(alpha0);
  double gradB = log(output) + gsl_sf_psi(b) - gsl_sf_psi(alpha0);

  return { gradA, gradB };
}
