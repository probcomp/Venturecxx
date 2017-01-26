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

#include "utils.h"

#include "types.h"
#include "values.h"

#include <cmath>
#include <gsl/gsl_randist.h>
#include <boost/lexical_cast.hpp>

vector<double> mapExpUptoMultConstant(const vector<double>& xs)
{
  vector<double> ps(xs.size());
  if (xs.empty()) { return ps; }
  double max = *std::max_element(xs.begin(), xs.end());

  for (size_t i = 0; i < xs.size(); ++i) {
    ps[i] = exp(xs[i] - max);
  }
  return ps;
}

double logSumExp(const vector<double>& xs)
{
  double sum = 0;
  if (xs.empty()) { return sum; }
  double max = *std::max_element(xs.begin(), xs.end());

  for (size_t i = 0; i < xs.size(); ++i) {
    sum += exp(xs[i] - max);
  }
  return max + log(sum);
}

size_t sampleCategorical(const vector<double> & ps, gsl_rng * rng)
{
  vector<unsigned int> ns(ps.size());
  gsl_ran_multinomial(rng, ps.size(), 1, &ps[0], &ns[0]);
  for (size_t i = 0; i < ns.size(); ++i) {
    if (ns[i] == 1) { return i; }
  }
  assert(false);
}

vector<double> computePartialSums(const vector<double>& xs)
{
  vector<double> sums(1, 0);
  for (size_t i = 0; i < xs.size(); ++i) {
    sums.push_back(sums.back() + xs[i]);
  }
  return sums;
}

size_t samplePartialSums(const vector<double> & sums, gsl_rng * rng)
{
  size_t lower = 0, upper = sums.size() - 1;
  double r = gsl_ran_flat(rng, sums[lower], sums[upper]);

  while (lower < upper - 1) {
    size_t mid = (lower + upper) / 2;
    if (r < sums[mid]) { upper = mid; }
    else { lower = mid; }
  }

  return lower;
}

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
  for (size_t i = 0; i < xs.size(); ++i) {
    if (sum < 0.000001) { ps.push_back(1.0/xs.size()); }
    else { ps.push_back(xs[i] / sum); }
    newSum += ps[i];
  }
  if (!(fabs(newSum - 1) < 0.01)) {
    cout << "sum: " << sum << endl;
    cout << "newSum: " << newSum << endl;
  }
  assert(fabs(newSum - 1) < 0.01);
  return ps;
}

size_t findVVPtr(
    const VentureValuePtr & val, const vector<VentureValuePtr>& vec)
{
  for (size_t i = 0; i < vec.size(); ++i) {
    if (vec[i]->equals(val)) { return i; }
  }
  return vec.size();
}

VentureValuePtr simulateCategorical(
    const Simplex & xs, const vector<VentureValuePtr> & os, gsl_rng * rng)
{
  Simplex ps = normalizeVector(xs);
  vector<unsigned int> ns(ps.size());
  gsl_ran_multinomial(rng, ps.size(), 1, &ps[0], &ns[0]);
  for (size_t i = 0; i < ns.size(); ++i) {
    if (ns[i] == 1) { return os[i]; }
  }
  assert(false);
}

double logDensityCategorical(const VentureValuePtr & val, const Simplex & xs)
{
  if (val->hasInt()) {
    Simplex ps = normalizeVector(xs);
    return log(ps[val->getInt()]);
  } else { return log(0.0); }
}

double logDensityCategorical(
    const VentureValuePtr & val,
    const Simplex & xs,
    const vector<VentureValuePtr> & os)
{
  Simplex ps = normalizeVector(xs);
  double answer = 0.0;
  for (size_t i = 0; i < os.size(); ++i) {
    if (os[i]->equals(val)) { answer += ps[i]; }
  }
  return log(answer);
}

// needs to go in the cxx, for an explanation see
// http://stackoverflow.com/questions/4445654/multiple-definition-of-template-specialization-when-using-different-objects
template <>
boost::python::object toPython<VentureValuePtr>(Trace * trace,
                                                const VentureValuePtr& v)
{
  return v->toPython(trace);
}

template <>
boost::python::object toPython<uint32_t>(Trace * trace, const uint32_t& st)
{
  boost::python::dict dict;
  dict["type"] = "number";
  dict["value"] = st;
  return dict;
}

template <>
boost::python::object toPython<double>(Trace * trace, const double& st)
{
  boost::python::dict dict;
  dict["type"] = "number";
  dict["value"] = st;
  return dict;
}

using boost::lexical_cast;

void checkArgsLength(
    const string & sp,
    const boost::shared_ptr<Args> & args,
    size_t expected)
{
  size_t length = args->operandValues.size();
  if (length != expected) {
    throw sp + " expects " + lexical_cast<string>(expected) +
      " arguments, not " + lexical_cast<string>(length);
  }
}

void checkArgsLength(
    const string & sp,
    const boost::shared_ptr<Args> & args,
    size_t lower,
    size_t upper)
{
  size_t length = args->operandValues.size();
  if (length < lower || length > upper) {
    throw sp + " expects between " + lexical_cast<string>(lower) + " and "
      + lexical_cast<string>(upper) + " arguments, not "
      + lexical_cast<string>(length);
  }
}

double
ran_log_gamma(gsl_rng *rng, double shape)
{
  if (shape < 1) {
    const double G = gsl_ran_gamma(rng, shape + 1, 1);
    const double U = gsl_rng_uniform(rng);
    return log(G) + log(U)/shape;
  } else {
    return log(gsl_ran_gamma(rng, shape, 1));
  }
}

double
logit(double x)
{
  return log(x/(1 - x));
}

double
logistic(double x)
{
  // For x <= -37, 1 + e^{-x} rounds to e^{-x}, so 1/(1 + e^{-x})
  // rounds to 1/e^{-x} = e^x.  For e < -709, e^{-x} would overflow
  // anyway, whereas e^x never will.
  if (x <= -37)
    return exp(x);
  else
    return 1/(1 + exp(-x));
}

double
log_logistic(double x)
{
  if (x <= -37)
    return x;
  else
    return -log1p(exp(-x));
}
