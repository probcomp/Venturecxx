#include <time.h>
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <iostream>
#include <cmath>
#include <cfloat>


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

double chain(gsl_rng * rng, int steps) {
  double mu_1 = 0.0;
  double sigma_1 = 1.0;
  double sigma_2 = 1.0;
  double x = gsl_ran_gaussian(rng, sigma_1) + mu_1;
  for (int i = 0; i < steps; i++) {
    // TODO If I were doing this for real, I would store w_old from
    // the previous loop iteration, not recompute it; but thus is what
    // Puma does.
    double w_old = NormalDistributionLogLikelihood(2.0, x, sigma_2);
    double x_new = gsl_ran_gaussian(rng, sigma_1) + mu_1;
    double w_new = NormalDistributionLogLikelihood(2.0, x_new, sigma_2);
    double alpha = w_new - w_old;
    double logU = log(gsl_ran_flat(rng,0.0,1.0));
    if (logU < alpha) {
      x = x_new;
    }
  }
  return x;
}

int main(int argc, char** argv) {
  int steps = atoi(argv[1]);
  int reps = atoi(argv[2]);
  std::cout << steps << "\n";
  gsl_rng * rng = gsl_rng_alloc(gsl_rng_mt19937);
  gsl_rng_set(rng, time(NULL));
  for (int i = 0; i < reps; i++) {
    std::cout << chain(rng, steps) << std::endl;
  }
}
