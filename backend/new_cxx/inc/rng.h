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

#ifndef RNG_H
#define RNG_H

#include <gsl/gsl_rng.h>

// A wrapper around GSL RNGs that has a C++-style destructor, so that
// it is OK to delete (as a shared pointer would do).
struct RNGbox {
  RNGbox(const gsl_rng_type* T) { rng = gsl_rng_alloc(T); }
  void set_seed(unsigned long int s) { gsl_rng_set(rng, s); }
  gsl_rng* get_rng() { return rng; }
  ~RNGbox() { gsl_rng_free(rng); }
private:
  gsl_rng * rng;
};
#endif
