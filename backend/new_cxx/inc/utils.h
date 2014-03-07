#ifndef UTILS_H
#define UTILS_H

#include "types.h"
#include <gsl/gsl_rng.h>

#include <cmath>
#include <boost/foreach.hpp>
#include <algorithm>
#include <numeric>

#include <boost/python/dict.hpp>

/* Maps exp over the vector, normalizing so that the maximum is 1. */
vector<double> mapExpUptoMultConstant(const vector<double>& xs);

/* Samples from an unnormalized sequence of probabilities. */
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

template <typename T>
vector<vector<T> > cartesianProduct(vector<vector<T> > sequences)
{
  vector<vector<T> > products;
  if (sequences.empty())
  {
    products.push_back(vector<T>());
  }
  else
  {
    vector<T> lastGroup = sequences.back();
    sequences.pop_back();
    vector<vector<T> > recursiveProduct = cartesianProduct(sequences);
    BOOST_FOREACH(vector<T> vs, recursiveProduct)
    {
      BOOST_FOREACH(T v, lastGroup)
      {
        vector<VentureValuePtr> new_vs(vs);
        new_vs.push_back(v);
        products.push_back(new_vs);
      }
    }
  }
  return products;
}

// Converts a C++ map to a python dict
template <class K, class V>
boost::python::dict toPythonDict(std::map<K, V>& map) {
  typename std::map<K, V>::iterator iter;
  boost::python::dict dictionary;
  for (iter = map.begin(); iter != map.end(); ++iter) {
    dictionary[iter->first] = iter->second;
  }
  return dictionary;
}

#endif
