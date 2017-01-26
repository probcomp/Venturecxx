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
VentureValuePtr NormalPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("normal", args, 2);

  double mu = args->operandValues[0]->getDouble();
  double sigma = args->operandValues[1]->getDouble();

  double x = gsl_ran_gaussian(rng, sigma) + mu;

  return VentureValuePtr(new VentureNumber(x));
}

double NormalPSP::simulateNumeric(const vector<double> & args, gsl_rng * rng) const
{
  double x = gsl_ran_gaussian(rng, args[1]) + args[0];
  if (!isfinite(x)) {
    cout << "Normal(" << args[0] << ", " << args[1] << ") = " << x << endl;
  }
  assert(isfinite(x));
  return x;
}

double NormalPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
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
  if (!isfinite(ld)) {
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
VentureValuePtr GammaPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("gamma", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = gsl_ran_gamma(rng, a, 1.0 / b);
  return VentureValuePtr(new VentureNumber(x));
}

double GammaPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return GammaDistributionLogLikelihood(x, a, b);
}

/* Inv Gamma */
VentureValuePtr InvGammaPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("inv_gamma", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = 1.0 / gsl_ran_gamma(rng, a, 1.0 / b);
  return VentureValuePtr(new VentureNumber(x));
}

double InvGammaPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return InvGammaDistributionLogLikelihood(x, a, b);
}

/* Exponential */
VentureValuePtr ExponentialPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("expon", args, 1);

  double theta = args->operandValues[0]->getDouble();

  double x = gsl_ran_exponential(rng, 1.0 / theta);
  return VentureValuePtr(new VentureNumber(x));
}

double ExponentialPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  double theta = args->operandValues[0]->getDouble();
  double x = value->getDouble();
  return ExponentialDistributionLogLikelihood(x, theta);
}

/* UniformContinuous */
VentureValuePtr UniformContinuousPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("uniform_continuous", args, 2);

  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();

  double x = gsl_ran_flat(rng, a, b);
  return VentureValuePtr(new VentureNumber(x));
}

double UniformContinuousPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  double a = args->operandValues[0]->getDouble();
  double b = args->operandValues[1]->getDouble();
  double x = value->getDouble();
  return log(gsl_ran_flat_pdf(x, a, b));
}

/* Beta */
VentureValuePtr BetaPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("beta", args, 2);

  const double a = args->operandValues[0]->getDouble();
  const double b = args->operandValues[1]->getDouble();
  double r;

  // Copypasta of BetaOutputPSP.simulate from lite/continuous.py.  See
  // references and commentary on the algorithm there.
  if (a == 0 && b == 0) {
    // Dirac deltas at 0 and 1.
    r = gsl_rng_get(rng) & 1;
  } else if (a == 0) {
    // Dirac delta at 1.
    r = 1;
  } else if (b == 0) {
    // Dirac delta at 0.
    r = 0;
  } else if (std::min(a, b) < 1e-300) {
    // Dirac deltas at 0 and 1 with magnitude ratio a/(a + b).
    r = 1 - gsl_ran_bernoulli(rng, a/(a + b));
  } else if (1 < a || 1 < b) {
    // Easy case: well-known reduction to G/(G + H) where G ~ Gamma(a)
    // and H ~ Gamma(b) are independent.
    const double g = gsl_ran_gamma(rng, a, 1);
    const double h = gsl_ran_gamma(rng, b, 1);
    r = g/(g + h);
  } else {
    // Johnk's algorithm
    for (;;) {
      const double u = gsl_rng_uniform(rng);
      const double v = gsl_rng_uniform(rng);
      const double x = pow(u, 1/a);
      const double y = pow(v, 1/b);
      if (1 < x + y)
	continue;		// reject
      if (0 < x + y) {
	r = x/(x + y);
	break;			// accept
      }

      assert(0 < u);
      assert(0 < v);
      double log_x = log(u)/a;
      double log_y = log(v)/b;
      assert(!isinf(log_x));
      assert(!isinf(log_y));
      const double log_m = std::max(log_x, log_y);
      log_x -= log_m;
      log_y -= log_m;
      r = exp(log_x - log(exp(log_x) + exp(log_y)));
      break;			// accept
    }
  }

  return VentureValuePtr(new VentureNumber(r));
}

double BetaPSP::simulateNumeric(const vector<double> & args, gsl_rng * rng) const
{
  assert(args[0] > 0);
  assert(args[1] > 0);
  double x = gsl_ran_beta(rng, args[0], args[1]);
  assert(isfinite(x));
  return x;
}

double BetaPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
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
  if (!isfinite(ld)) {
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

/* Log of Beta */
VentureValuePtr
LogBetaPSP::simulate(const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("log_beta", args, 2);

  const double inf = std::numeric_limits<double>::infinity();
  const double a = args->operandValues[0]->getDouble();
  const double b = args->operandValues[1]->getDouble();
  double r;

  if (a == 0 && b == 0) {
    r = (gsl_rng_get(rng) & 1) ? -inf : 0;
  } else if (a == 0) {
    r = -inf;
  } else if (b == 0) {
    r = 0;
  } else if (std::min(a, b) < 1e-300) {
    r = gsl_ran_bernoulli(rng, a/(a + b)) ? 0 : -inf;
  } else {
    const double log_g = ran_log_gamma(rng, a);
    const double log_h = ran_log_gamma(rng, b);
    assert(!isinf(log_g));
    assert(!isinf(log_h));
    vector<double> log_gh(2);
    log_gh[0] = log_g;
    log_gh[1] = log_h;
    r = log_g - logSumExp(log_gh);
  }

  return VentureValuePtr(new VentureNumber(r));
}

double
LogBetaPSP::logDensity(
    const VentureValuePtr & value, const shared_ptr<Args> & args) const
{
  checkArgsLength("log_beta", args, 2);

  const double x = value->getDouble();
  const double a = args->operandValues[0]->getDouble();
  const double b = args->operandValues[1]->getDouble();

  // x = log y for a beta sample y, so its density is the beta density
  // of y = e^x with the Jacobian dy/dx = e^x:
  //
  //	log p(x | a, b) = log [p(y | a, b) dy/dx]
  //	= (a - 1) log y + (b - 1) log (1 - y) - log Beta(a, b) + log dy/dx
  //	= (a - 1) log e^x + (b - 1) log (1 - e^x) - log B(a, b) + log e^x
  //	= (a - 1) x + (b - 1) log (1 - e^x) - log B(a, b) + x
  //	= a x + (b - 1) log (1 - e^x) - log B(a, b).
  //
  return a*x + (b - 1)*log1p(-exp(x)) - gsl_sf_lnbeta(a, b);
}

vector<double>
LogBetaPSP::gradientOfLogDensity(double x, const vector<double> & args) const
{
  const double a = args[0];
  const double b = args[1];

  // const double d_x = a - (b - 1)/expm1(-x);
  const double d_a = x + gsl_sf_psi(a + b) - gsl_sf_psi(a);
  const double d_b = log1p(-exp(x)) + gsl_sf_psi(a + b) - gsl_sf_psi(b);

  vector<double> d(2);
  d.at(0) = d_a;
  d.at(1) = d_b;
  return d;
}

/* Log-odds of beta */
VentureValuePtr
LogOddsBetaPSP::simulate(const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("log_odds_beta", args, 2);

  const double inf = std::numeric_limits<double>::infinity();
  const double a = args->operandValues[0]->getDouble();
  const double b = args->operandValues[1]->getDouble();
  double r;

  if (a == 0 && b == 0) {
    r = (gsl_rng_get(rng) & 1) ? -inf : +inf;
  } else if (a == 0) {
    r = -inf;
  } else if (b == 0) {
    r = +inf;
  } else if (std::min(a, b) < 1e-300) {
    r = gsl_ran_bernoulli(rng, a/(a + b)) ? +inf : -inf;
  } else if (std::min(a, b) < 1) {
    const double log_g = ran_log_gamma(rng, a);
    const double log_h = ran_log_gamma(rng, b);
    assert(!isinf(log_g));
    assert(!isinf(log_h));
    r = log_g - log_h;
  } else {
    assert(1 <= std::min(a, b));
    const double g = gsl_ran_gamma(rng, a, 1);
    const double h = gsl_ran_gamma(rng, b, 1);
    assert(g != 0);
    assert(h != 0);
    r = log(g/h);
  }

  return VentureValuePtr(new VentureNumber(r));
}

double
LogOddsBetaPSP::logDensity(
    const VentureValuePtr & value, const shared_ptr<Args> & args) const
{
  checkArgsLength("log_odds_beta", args, 2);

  const double x = value->getDouble();
  const double a = args->operandValues[0]->getDouble();
  const double b = args->operandValues[1]->getDouble();

  return a*log_logistic(x) + b*log_logistic(-x) - gsl_sf_lnbeta(a, b);
}

vector<double>
LogOddsBetaPSP::gradientOfLogDensity(
    double x, const vector<double> & args) const
{
  const double a = args[0];
  const double b = args[1];

  // const double d_x = a*logistic(-x) - b*logistic(x);
  const double d_a = log_logistic(x) + gsl_sf_psi(a + b) - gsl_sf_psi(a);
  const double d_b = log_logistic(-x) + gsl_sf_psi(a + b) - gsl_sf_psi(b);

  vector<double> d(2);
  d.at(0) = d_a;
  d.at(1) = d_b;
  return d;
}

/* Student-t */
VentureValuePtr StudentTPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
//  checkArgsLength("student_t", args, 1);

  double nu = args->operandValues[0]->getDouble();
  double loc = 0; if (args->operandValues.size() > 1) { loc = args->operandValues[1]->getDouble(); }
  double shape = 1; if (args->operandValues.size() > 2) { shape = args->operandValues[2]->getDouble(); }

  double x = gsl_ran_tdist(rng, nu);
  return VentureValuePtr(new VentureNumber((shape * x) + loc));
}

double StudentTPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  double nu = args->operandValues[0]->getDouble();
  double loc = 0; if (args->operandValues.size() > 1) { loc = args->operandValues[1]->getDouble(); }
  double shape = 1; if (args->operandValues.size() > 2) { shape = args->operandValues[2]->getDouble(); }

  double x = value->getDouble();
  double y = (x - loc) / shape;
  // TODO: compute in logspace
  return log(gsl_ran_tdist_pdf(y, nu) / shape);
}

VentureValuePtr ChiSquaredPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("chi_sq", args, 1);

  double nu = args->operandValues[0]->getDouble();

  double x = gsl_ran_chisq(rng, nu);
  return VentureValuePtr(new VentureNumber(x));
}

double ChiSquaredPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  double nu = args->operandValues[0]->getDouble();
  double x = value->getDouble();
  return ChiSquaredDistributionLogLikelihood(x, nu);
}

VentureValuePtr InvChiSquaredPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
{
  checkArgsLength("inv_chi_sq", args, 1);

  double nu = args->operandValues[0]->getDouble();

  double x = 1.0 / gsl_ran_chisq(rng, nu);
  return VentureValuePtr(new VentureNumber(x));
}

double InvChiSquaredPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  double nu = args->operandValues[0]->getDouble();
  double x = value->getDouble();
  return InvChiSquaredDistributionLogLikelihood(x, nu);
}

VentureValuePtr ApproximateBinomialPSP::simulate(
    const shared_ptr<Args> & args, gsl_rng * rng) const
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

double ApproximateBinomialPSP::logDensity(
    const VentureValuePtr & value,
    const shared_ptr<Args> & args) const
{
  double n = args->operandValues[0]->getDouble();
  double p = args->operandValues[1]->getDouble();

  double mean = n * p;
  double sigma = sqrt(n * (p - p * p));

  double x = value->getDouble();

  return NormalDistributionLogLikelihood(x, mean, sigma);
}
