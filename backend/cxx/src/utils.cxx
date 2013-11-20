/*
* Copyright (c) 2013, MIT Probabilistic Computing Project.
* 
* This file is part of Venture.
* 
* Venture is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
* 
* Venture is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
* 
* You should have received a copy of the GNU General Public License along with Venture.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "utils.h"
#include <cmath>
#include <cassert>
#include <iostream>

#include "value.h"
#include "all.h"

#include <vector>
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

void listShallowDestroy(VentureList * list)
{
  VenturePair * pair = dynamic_cast<VenturePair*>(list);
  if (pair) { listShallowDestroy(pair->rest); }
  delete list;
}

VentureValue * listRef(VentureList * list,size_t n)
{
  if (n == 0)
  {
    VenturePair * pair = dynamic_cast<VenturePair*>(list);
    assert(pair);
    return pair->first;
  }
  else
  {
    VenturePair * pair = dynamic_cast<VenturePair*>(list);
    assert(pair);
    return listRef(pair->rest,n-1);
  }
}

size_t listLength(VentureList * list)
{
  if (dynamic_cast<VentureNil*>(list)) 
  { 
    return 0; 
  }
  else
  {
    VenturePair * pair = dynamic_cast<VenturePair*>(list);
    assert(pair);
    return 1 + listLength(pair->rest);
  }
}

double sumVector(const vector<double> & xs)
{
  double sum = 0;
  for (double x : xs) { sum += x; }
  return sum;
}

void normalizeVector(vector<double> & xs)
{
  double sum = sumVector(xs);
  double newSum = 0;
  for (size_t i = 0; i < xs.size(); ++i)
  {
    if (sum < 0.000001) { xs[i] = 1.0/xs.size(); }
    else { xs[i] /= sum; }
    newSum += xs[i];
  }
  if (!(fabs(newSum - 1) < 0.01))
  { 
    cout << "sum: " << sum << endl;
    cout << "newSum: " << newSum << endl;
  }
  assert(fabs(newSum - 1) < 0.01);
}

void destroyExpression(VentureValue * exp)
{
  VenturePair * pair = dynamic_cast<VenturePair*>(exp);
  if (pair)
  {
    destroyExpression(pair->first);
    destroyExpression(pair->rest);
  }
  delete exp;
}



uint32_t sampleCategorical(vector<double> xs, gsl_rng * rng)
{
  normalizeVector(xs);
  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < xs.size(); ++i)
  {
    sum += xs[i];
    if (u <= sum) { return i; }
  }
  assert(false);
  return -1;
}
