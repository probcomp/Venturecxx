#include "stathelpers.h"
#include "value.h"
#include <vector>

#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

uint32_t sampleCategorical(const vector<double> & xs, gsl_rng * rng)
{
  double u = gsl_ran_flat(rng,0.0,1.0);
  double sum = 0.0;
  for (size_t i = 0; i < xs.size(); ++i)
  {
    sum += xs[i];
    if (u < sum) { return i; }
  }
  assert(false);
  return -1;
}
