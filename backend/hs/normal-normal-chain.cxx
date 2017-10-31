#include <time.h>
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <cfloat>
#include <cmath>
#include <cstring>
#include <iostream>


double NormalDistributionLogLikelihood(double sampled_value, double average, double sigma) {
  double loglikelihood = 0.0;
  loglikelihood -= log(sigma);
  // TODO If I were doing this for real, I would compute this constant
  // at most once, but this is what Puma does.  Is gcc smart enough to
  // constant-fold this?
  loglikelihood -= 0.5 * log(2.0 * 3.14159265358979323846264338327950);
  double deviation = sampled_value - average;
  loglikelihood -= 0.5 * deviation * deviation / (sigma * sigma);
  return loglikelihood;
}

double mu_1 = 0.0;
double sigma_1 = 1.0;
double sigma_2 = 1.0;
double log_bound = log(0.5); // Guess upper bound for unit Gaussian

double rejection(gsl_rng * rng, double obs) {
  while (true) {
    double x = gsl_ran_gaussian(rng, sigma_1) + mu_1;
    double w = NormalDistributionLogLikelihood(obs, x, sigma_2);
    double logU = log(gsl_ran_flat(rng,0.0,1.0));
    if (logU < w - log_bound) {
      return x;
    }
  }
}

double chain(gsl_rng * rng, double obs, int steps) {
  double x = gsl_ran_gaussian(rng, sigma_1) + mu_1;
  for (int i = 0; i < steps; i++) {
    // TODO If I were doing this for real, I would store w_old from
    // the previous loop iteration, not recompute it; but this is what
    // Puma does.
    double w_old = NormalDistributionLogLikelihood(obs, x, sigma_2);
    double x_new = gsl_ran_gaussian(rng, sigma_1) + mu_1;
    double w_new = NormalDistributionLogLikelihood(obs, x_new, sigma_2);
    double alpha = w_new - w_old;
    double logU = log(gsl_ran_flat(rng,0.0,1.0));
    if (logU < alpha) {
      x = x_new;
    }
  }
  return x;
}

int main(int argc, char** argv) {
  char* mode = argv[1];
  int reps = atoi(argv[2]);
  int steps = atoi(argv[3]);
  gsl_rng * rng = gsl_rng_alloc(gsl_rng_mt19937);
  gsl_rng_set(rng, time(NULL));
  std::cerr << mode << " " << reps << " " << steps << std::endl;
  if (strcmp(mode, "rejection") == 0) {
    for (int i = 0; i < reps; i++) {
      std::cout << rejection(rng, 2.0) << std::endl;
    }
  }
  if (strcmp(mode, "mcmc") == 0) {
    for (int i = 0; i < reps; i++) {
      std::cout << chain(rng, 2.0, steps) << std::endl;
    }
  }
}
