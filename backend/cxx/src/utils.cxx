#include "utils.h"
#include <cmath>
#include <cassert>
#include <iostream>

#include "value.h"
#include "all.h"



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
    if (sum == 0) { xs[i] = 1.0/xs.size(); }
    else { xs[i] /= sum; }
    newSum += xs[i];
  }
  if (fabs(newSum - 1) > 0.01) 
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
