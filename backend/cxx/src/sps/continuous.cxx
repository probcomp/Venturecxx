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
  double mu;
  VentureNumber * vmu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  if (vmu) { mu = vmu->x; }
  else
  {
    VentureAtom * vcmu = dynamic_cast<VentureAtom*>(operands[0]->getValue());
    assert(vcmu);
    mu = vcmu->n;
  }

  VentureNumber * vmu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * vsigma = dynamic_cast<VentureNumber *>(operands[1]->getValue());
  assert(vmu);
  assert(vsigma);
  double x = gsl_ran_gaussian(rng, vsigma->x) + vmu->x;
  return new VentureNumber(x);
}

double NormalSP::simulateOutputNumeric(const vector<double> & args, gsl_rng * rng)  const
{
  double x = gsl_ran_gaussian(rng, args[1]) + args[0];
  assert(isfinite(x));
  return x;
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
  assert(isfinite(args[0]));
  assert(isfinite(args[1]));
  assert(isfinite(output));
  assert(args[1] > 0);
  double ld = log(gsl_ran_gaussian_pdf(output - args[0], args[1]));
  if (!isfinite(ld))
  {
    cout << "Normal(" << args[0] << ", " << args[1] << ") = " << output << " <" << ld << ">" << endl;
  }
  assert(isfinite(ld));
  return ld;
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
  if (x == 1.0) { x = 0.99; }
  return new VentureNumber(x);
}

double BetaSP::simulateOutputNumeric(const vector<double> & args, gsl_rng * rng) const
{
  assert(args[0] > 0);
  assert(args[1] > 0);
  double x = gsl_ran_beta(rng,args[0],args[1]);
  assert(isfinite(x));
  // TODO FIXME GSL NUMERIC
  if (x == 1.0) { return 0.99; }
  else { return x; }
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
  assert(args[0] > 0);
  assert(args[1] > 0);
  assert(0 <= output);
  assert(output <= 1);
  double ld = log(gsl_ran_beta_pdf(output,args[0],args[1]));
  if (!isfinite(ld))
  {
    cout << "Beta(" << args[0] << ", " << args[1] << ") = " << output << " <" << ld << ">" << endl;
  }

  assert(isfinite(ld));
  return ld;
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

  double gradA = log(output) + gsl_sf_psi(alpha0) - gsl_sf_psi(a);
  double gradB = log(output) + gsl_sf_psi(alpha0) - gsl_sf_psi(b);

  return { gradA, gradB };
}

/* Student-t */
VentureValue * StudentTSP::simulateOutput(Node * node, gsl_rng * rng)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * nu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  assert(nu);
  double x = gsl_ran_tdist(rng,nu->x);
  return new VentureNumber(x);
}

double StudentTSP::logDensityOutput(VentureValue * value, Node * node)  const
{
  vector<Node *> & operands = node->operandNodes;
  VentureNumber * nu = dynamic_cast<VentureNumber *>(operands[0]->getValue());
  VentureNumber * x = dynamic_cast<VentureNumber *>(value);
  assert(nu);
  assert(x);
  return log(gsl_ran_tdist_pdf(x->x,nu->x));
}
