#include <time.h>
#include <gsl/gsl_rng.h>
#include <gsl/gsl_randist.h>

#include <algorithm>
#include <cfloat>
#include <cmath>
#include <cstring>
#include <iostream>
#include <vector>

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

template<typename T>
T simulate_categorical_normalized(
    gsl_rng * rng, const std::vector<T>& xs, const std::vector<double>& ps) {
  std::vector<unsigned int> ns(ps.size());
  gsl_ran_multinomial(rng, ps.size(), 1, &ps[0], &ns[0]);
  for (size_t i = 0; i < ns.size(); ++i) {
    if (ns[i] == 1) { return xs[i]; }
  }
}

double logsumexp(const std::vector<double>& logs) {
  if (logs.empty()) { return log(0.0); }
  double max = *std::max_element(logs.begin(), logs.end());
  double sum = 0;
  for (size_t i = 0; i < logs.size(); ++i) {
    sum += exp(logs[i] - max);
  }
  return max + log(sum);
}

template<typename T>
T simulate_log_categorical(
    gsl_rng * rng, const std::vector<T>& xs, const std::vector<double>& ws) {
  double total_w = logsumexp(ws);
  std::vector<double> ps = std::vector<double>(ws.size());
  for (int i = 0; i < ws.size(); i++) {
    ps[i] = exp(ws[i] - total_w);
  }
  return simulate_categorical_normalized(rng, xs, ps);
}

double importance(gsl_rng * rng, double obs, int particles) {
  std::vector<double> xs = std::vector<double>(particles);
  std::vector<double> ws = std::vector<double>(particles);
  for (int i = 0; i < particles; i++) {
    xs[i] = gsl_ran_gaussian(rng, sigma_1) + mu_1;
    ws[i] = NormalDistributionLogLikelihood(obs, xs[i], sigma_2);
  }
  return simulate_log_categorical(rng, xs, ws);
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
  double obs = atof(argv[1]);
  char* mode = argv[2];
  int reps = atoi(argv[3]);
  int steps = atoi(argv[4]);
  gsl_rng * rng = gsl_rng_alloc(gsl_rng_mt19937);
  gsl_rng_set(rng, time(NULL));
  std::cerr << mode << " " << reps << " " << steps << std::endl;
  if (strcmp(mode, "rejection") == 0) {
    for (int i = 0; i < reps; i++) {
      std::cout << rejection(rng, obs) << std::endl;
    }
  }
  if (strcmp(mode, "importance") == 0) {
    for (int i = 0; i < reps; i++) {
      std::cout << importance(rng, obs, steps) << std::endl;
    }
  }
  if (strcmp(mode, "mcmc") == 0) {
    for (int i = 0; i < reps; i++) {
      std::cout << chain(rng, obs, steps) << std::endl;
    }
  }
}
