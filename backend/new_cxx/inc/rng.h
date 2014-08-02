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
