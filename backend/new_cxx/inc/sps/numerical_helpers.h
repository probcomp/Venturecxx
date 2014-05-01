#ifndef SPS_NUMERICAL_HELPERS_H
#define SPS_NUMERICAL_HELPERS_H

double NormalDistributionLogLikelihood(double sampled_value, double average, double sigma);
double GammaDistributionLogLikelihood(double sampled_value, double alpha, double beta);
double InvGammaDistributionLogLikelihood(double sampled_value, double alpha, double beta);
double BetaDistributionLogLikelihood(double sampled_value, double alpha, double beta);
double ChiSquaredDistributionLogLikelihood(double sampled_value, double nu);
double InvChiSquaredDistributionLogLikelihood(double sampled_value, double nu);
double PoissonDistributionLogLikelihood(int sampled_value_count, double lambda);
#endif
