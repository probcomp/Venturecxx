// Copyright (c) 2013, 2014, 2015 MIT Probabilistic Computing Project.
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

#include "sps/continuous.h"
#include "sps/numerical_helpers.h"
#include "args.h"
#include "values.h"
#include "utils.h"

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>
#include <cmath>
#include <cfloat>

using std::isfinite;


/* Normal */
VentureValuePtr NormalPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("normal", args, 2);

  double mu = args->operandValues[0]->getDouble();
  double sigma = args->operandValues[1]->getDouble();

  double x = gsl_ran_gaussian(rng, sigma) + mu;

  return VentureValuePtr(new VentureNumber(x));
}

double NormalPSP::simulateNumeric(const vector<double> & args, gsl_rng * rng)  const
{
  double x = gsl_ran_gaussian(rng, args[1]) + args[0];
  if (!isfinite(x))
  {
    cout << "Normal(" << args[0] << ", " << args[1] << ") = " << x << endl;
  }
  assert(isfinite(x));
  return x;
}

double NormalPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double mu = args->operandValues[0]->getDouble();
  double sigma = args->operandValues[1]->getDouble();
  double x = value->getDouble();

  return NormalDistributionLogLikelihood(x, mu, sigma);
}

double NormalPSP::logDensityNumeric(double output, const vector<double> & args) const
{
  assert(isfinite(args[0]));
  assert(isfinite(args[1]));
  assert(isfinite(output));
  assert(args[1] > 0);
  double ld = NormalDistributionLogLikelihood(output, args[0], args[1]);
  if (!isfinite(ld))
  {
    cout << "Normal(" << args[0] << ", " << args[1] << ") = " << output << " <" << ld << ">" << endl;
  }
  assert(isfinite(ld));
  return ld;
}

/*
vector<ParameterScope> NormalPSP::getParameterScopes() const
{
  return {ParameterScope::REAL, ParameterScope::POSITIVE_REAL};
}
*/

vector<double> NormalPSP::gradientOfLogDensity(double output,
					      const vector<double> & arguments) const
{
  double mu = arguments[0];
  double sigma = arguments[1];
  double x = output;

  double gradMu = (x - mu) / (sigma * sigma);
  double gradSigma = (((x - mu) * (x - mu)) - (sigma * sigma)) / (sigma * sigma * sigma);

  vector<double> ret;
  ret.push_back(gradMu);
  ret.push_back(gradSigma);
  return ret;
}

/* Gamma */
VentureValuePtr GammaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("gamma", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = gsl_ran_gamma(rng, a, 1.0 / b);
  return VentureValuePtr(new VentureNumber(x));
}

double GammaPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return GammaDistributionLogLikelihood(x, a, b);
}

/* Inv Gamma */
VentureValuePtr InvGammaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("inv_gamma", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = 1.0 / gsl_ran_gamma(rng, a, 1.0 / b);
  return VentureValuePtr(new VentureNumber(x));
}

double InvGammaPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return InvGammaDistributionLogLikelihood(x, a, b);
}

/* Exponential */
VentureValuePtr ExponentialPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("expon", args, 1);

  double theta = args->operandValues[0]->getDouble();

  double x = gsl_ran_exponential(rng, 1.0 / theta);
  return VentureValuePtr(new VentureNumber(x));
}

double ExponentialPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double theta = args->operandValues[0]->getDouble();
  double x = value->getDouble();
  return ExponentialDistributionLogLikelihood(x,theta);
}

/* UniformContinuous */
VentureValuePtr UniformContinuousPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("uniform_continuous", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = gsl_ran_flat(rng,a,b);
  return VentureValuePtr(new VentureNumber(x));
}

double UniformContinuousPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return log(gsl_ran_flat_pdf(x,a,b));
}

/* Beta */
VentureValuePtr BetaPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
  checkArgsLength("beta", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = gsl_ran_beta(rng,a,b);
  if (x > .99) { x = 0.99; }
  if (x < 0.01) { x = 0.01; }

  return VentureValuePtr(new VentureProbability(x));
}

double BetaPSP::simulateNumeric(const vector<double> & args, gsl_rng * rng) const
{
  assert(args[0] > 0);
  assert(args[1] > 0);
  double x = gsl_ran_beta(rng,args[0],args[1]);
  assert(isfinite(x));
  // TODO FIXME GSL NUMERIC
  if (x > .99) { x = 0.99; }
  if (x < 0.01) { x = 0.01; }
  return x;
}

double BetaPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getProbability();
  return BetaDistributionLogLikelihood(x, a, b);
}

double BetaPSP::logDensityNumeric(double output, const vector<double> & args) const
{
  assert(args[0] > 0);
  assert(args[1] > 0);
  assert(0 <= output);
  assert(output <= 1);
  double ld = BetaDistributionLogLikelihood(output, args[0], args[1]);
  if (!isfinite(ld))
  {
    cout << "Beta(" << args[0] << ", " << args[1] << ") = " << output << " <" << ld << ">" << endl;
  }

  assert(isfinite(ld));
  return ld;
}

/*
vector<ParameterScope> BetaPSP::getParameterScopes() const
{
  return {ParameterScope::POSITIVE_REAL, ParameterScope::POSITIVE_REAL};
}
*/

vector<double> BetaPSP::gradientOfLogDensity(double output,
					      const vector<double> & arguments) const
{
  double a = arguments[0];
  double b = arguments[1];

  double alpha0 = a + b;

  double gradA = log(output) + gsl_sf_psi(alpha0) - gsl_sf_psi(a);
  double gradB = log(output) + gsl_sf_psi(alpha0) - gsl_sf_psi(b);

  assert(isfinite(gradA));
  assert(isfinite(gradB));

  vector<double> ret;
  ret.push_back(gradA);
  ret.push_back(gradB);
  return ret;

}

/* Student-t */
VentureValuePtr StudentTPSP::simulate(shared_ptr<Args> args, gsl_rng * rng)  const
{
//  checkArgsLength("student_t", args, 1);

  double nu = args->operandValues[0]->getDouble();
  double loc = 0; if (args->operandValues.size() > 1) { loc = args->operandValues[1]->getDouble(); }
  double shape = 1; if (args->operandValues.size() > 2) { shape = args->operandValues[2]->getDouble(); }

  double x = gsl_ran_tdist(rng,nu);
  return VentureValuePtr(new VentureNumber((shape * x) + loc));
}

double StudentTPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args)  const
{
  double nu = args->operandValues[0]->getDouble();
  double loc = 0; if (args->operandValues.size() > 1) { loc = args->operandValues[1]->getDouble(); }
  double shape = 1; if (args->operandValues.size() > 2) { shape = args->operandValues[2]->getDouble(); }

  double x = value->getDouble();
  double y = (x - loc) / shape;
  // TODO: compute in logspace
  return log(gsl_ran_tdist_pdf(y,nu) / shape);
}

VentureValuePtr ChiSquaredPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("chi_sq", args, 1);

  double nu = args->operandValues[0]->getDouble();

  double x = gsl_ran_chisq(rng,nu);
  return VentureValuePtr(new VentureNumber(x));
}

double ChiSquaredPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double nu = args->operandValues[0]->getDouble();
  double x = value->getDouble();
  return ChiSquaredDistributionLogLikelihood(x,nu);
}

VentureValuePtr InvChiSquaredPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("inv_chi_sq", args, 1);

  double nu = args->operandValues[0]->getDouble();

  double x = 1.0 / gsl_ran_chisq(rng,nu);
  return VentureValuePtr(new VentureNumber(x));
}

double InvChiSquaredPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double nu = args->operandValues[0]->getDouble();
  double x = value->getDouble();
  return InvChiSquaredDistributionLogLikelihood(x,nu);
}

VentureValuePtr ApproximateBinomialPSP::simulate(shared_ptr<Args> args, gsl_rng * rng) const
{
  checkArgsLength("approx_binomial", args, 2);

  double n = args->operandValues[0]->getDouble();
  double p = args->operandValues[1]->getDouble();

  double mean = n * p;
  double sigma = sqrt(n * (p - p * p));

  double x;
  do {
    x = gsl_ran_gaussian(rng, sigma) + mean;
  } while (x < 0);

  return VentureValuePtr(new VentureNumber(x));
}

double ApproximateBinomialPSP::logDensity(VentureValuePtr value, shared_ptr<Args> args) const
{
  double n = args->operandValues[0]->getDouble();
  double p = args->operandValues[1]->getDouble();

  double mean = n * p;
  double sigma = sqrt(n * (p - p * p));

  double x = value->getDouble();

  return NormalDistributionLogLikelihood(x,mean,sigma);
}
