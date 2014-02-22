#ifndef UTILS_H
#define UTILS_H

#include "types.h"
#include <gsl/gsl_rng.h>

#include <cmath>
#include <boost/foreach.hpp>
#include <algorithm>
#include <numeric>

/* Maps exp over the vector, normalizing so that the maximum is 1. */
vector<double> mapExp(const vector<double>& xs);

/* Samples given the partial sums of an unnormalized sequence of probabilities. */
size_t sampleCategorical(const vector<double> & ps, gsl_rng * rng);

/* Computes the partial sums, including an initial zero. */
vector<double> computePartialSums(const vector<double>& xs);

/* Samples given the partial sums of an unnormalized sequence of probabilities. */
size_t samplePartialSums(const vector<double> & sums, gsl_rng * rng);

/**
 * Find the log of the sum of the exponents.
 * Is careful about numerical underflow.
 */
double logaddexp(const vector<double>& xs);

double sumVector(const vector<double> & xs);
Simplex normalizeVector(const vector<double> & xs);

VentureValuePtr simulateCategorical(const Simplex & ps, gsl_rng * rng);
VentureValuePtr simulateCategorical(const Simplex & ps,const vector<VentureValuePtr> & os, gsl_rng * rng);

double logDensityCategorical(VentureValuePtr val, const Simplex & ps);
double logDensityCategorical(VentureValuePtr val, const Simplex & ps,const vector<VentureValuePtr> & os);

vector<vector<VentureValuePtr> > cartesianProduct(vector<vector<VentureValuePtr> > original);


#endif
