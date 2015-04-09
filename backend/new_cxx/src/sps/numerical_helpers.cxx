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

#include "sps/numerical_helpers.h"
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>
#include <gsl/gsl_sf.h>

#include <cmath>
#include <cfloat>

// LogLikelihoods, from Yura's Utilities.cpp

using std::isfinite;

double NormalDistributionLogLikelihood(double sampled_value, double average, double sigma) {
  double loglikelihood = 0.0;
  loglikelihood -= log(sigma);
  loglikelihood -= 0.5 * log(2.0 * 3.14159265358979323846264338327950);
  double deviation = sampled_value - average;
  loglikelihood -= 0.5 * deviation * deviation / (sigma * sigma);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double GammaDistributionLogLikelihood(double sampled_value, double alpha, double beta) {
  //b^a * x^{a-1} * e^{-b * x} / Gamma(a)
  if (sampled_value <= 0.0) {
    return log(0.0);
  }
  double loglikelihood = alpha * log(beta);
  loglikelihood += (alpha - 1.0) * log(sampled_value);
  loglikelihood -= beta * sampled_value;
  loglikelihood -= gsl_sf_lngamma(alpha);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double InvGammaDistributionLogLikelihood(double sampled_value, double alpha, double beta) {
  //b^a * x^{-a-1} * e^{-b / x} / Gamma(a)
  double loglikelihood = alpha * log(beta);
  loglikelihood -= (alpha + 1.0) * log(sampled_value);
  loglikelihood -= beta / sampled_value;
  loglikelihood -= gsl_sf_lngamma(alpha);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }

  return loglikelihood;
}

double ExponentialDistributionLogLikelihood(double sampled_value, double theta) {
  //theta * e^{-theta * x}
  double loglikelihood = log(theta) - theta * sampled_value;
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double BetaDistributionLogLikelihood(double sampled_value, double alpha, double beta) {
  //x^{a-1} * (1-x)^{b-1} / Beta(a, b)
  double loglikelihood = 0.0;
  loglikelihood += (alpha - 1.0) * log(sampled_value);
  loglikelihood += (beta - 1.0) * log(1.0 - sampled_value);
  loglikelihood -= gsl_sf_lnbeta(alpha, beta);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double ChiSquaredDistributionLogLikelihood(double sampled_value, double nu) {
  //(x / 2)^{nu/2 - 1} * e^{-x/2} / (2 * Gamma(nu / 2))
  double loglikelihood = (0.5 * nu - 1.0) * log(0.5 * sampled_value);
  loglikelihood -= 0.5 * sampled_value;
  loglikelihood -= log(2.0);
  loglikelihood -= gsl_sf_lngamma(0.5 * nu);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

double InvChiSquaredDistributionLogLikelihood(double sampled_value, double nu) {
  //(2x)^{-nu/2 - 1} * e^{-1/2x} / (2 * Gamma(nu / 2))
  double loglikelihood = (-0.5 * nu  - 1.0) * log(2.0 * sampled_value);
  loglikelihood -= 0.5 / sampled_value;
  loglikelihood -= log(2.0);
  loglikelihood -= gsl_sf_lngamma(0.5 * nu);
  if (!isfinite(loglikelihood)) { loglikelihood = -DBL_MAX; }
  return loglikelihood;
}

// Discrete
double PoissonDistributionLogLikelihood(int sampled_value_count, double lambda) {
  //l^k * e^{-l} / k!
  double loglikelihood = 0.0;
  if (sampled_value_count > 0)
  {
    loglikelihood = sampled_value_count * log(lambda);
    loglikelihood -= gsl_sf_lnfact(sampled_value_count);
  }
  loglikelihood -= lambda;
  return loglikelihood;
}

