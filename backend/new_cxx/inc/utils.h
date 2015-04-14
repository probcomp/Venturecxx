// Copyright (c) 2014 MIT Probabilistic Computing Project.
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

#ifndef UTILS_H
#define UTILS_H

#include "types.h"
#include "value.h"
#include "args.h"

#include <gsl/gsl_rng.h>
#include <cmath>
#include <algorithm>
#include <numeric>

#include <boost/foreach.hpp>
#include <boost/python/dict.hpp>
#include <boost/python/list.hpp>

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
double logSumExp(const vector<double>& xs);

double sumVector(const vector<double> & xs);
Simplex normalizeVector(const vector<double> & xs);

size_t findVVPtr(VentureValuePtr val, const vector<VentureValuePtr>& vec);

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

template <class T>
boost::python::object toPython(Trace * trace, const T& t)
{ 
  return boost::python::object(t);
}

// Converts a C++ map to a python dict
template <class Map>
boost::python::dict toPythonDict(Trace * trace, const Map& map) {
  boost::python::dict dict;
  BOOST_FOREACH(const typename Map::value_type& pair, map)
  {
    dict[toPython(trace, pair.first)["value"]] = toPython(trace, pair.second);
  }
  return dict;
}

// Converts a C++ vector to a python list
template <class T>
boost::python::list toPythonList(Trace * trace, const vector<T>& vec) {
  boost::python::list list;
  BOOST_FOREACH(const T& v, vec)
  {
    list.append(toPython(trace, v));
  }
  return list;
}

void checkArgsLength(const string& sp, const shared_ptr<Args> args, size_t expected);
void checkArgsLength(const string& sp, const shared_ptr<Args> args, size_t lower, size_t upper);

#endif
