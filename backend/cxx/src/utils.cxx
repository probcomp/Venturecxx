#include "utils.h"
#include <cmath>
#include <cassert>

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
    xs[i] /= sum;
    newSum += xs[i];
  }
  assert(fabs(newSum - 1) < .01);
}
