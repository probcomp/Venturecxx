#ifndef STAT_HELPERS_H
#define STAT_HELPERS_H

#include "all.h"
#include <vector>
#include <cstdint>
#include <gsl/gsl_rng.h>

uint32_t sampleCategorical(const vector<double> & xs, gsl_rng * rng);





#endif
