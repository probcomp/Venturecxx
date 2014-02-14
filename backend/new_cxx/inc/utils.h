#ifndef UTILS_H
#define UTILS_H

#include "types.h"
#include <gsl/gsl_rng.h>

#include <cmath>

double sumVector(const vector<double> & xs);
Simplex normalizeVector(const vector<double> & xs);


VentureValuePtr simulateCategorical(const Simplex & ps, gsl_rng * rng);
VentureValuePtr simulateCategorical(const Simplex & ps,const vector<VentureValuePtr> & os, gsl_rng * rng);

double logDensityCategorical(VentureValuePtr val, const Simplex & ps);
double logDensityCategorical(VentureValuePtr val, const Simplex & ps,const vector<VentureValuePtr> & os);

#endif
